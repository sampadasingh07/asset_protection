

import io
import os
import logging
from datetime import datetime
from uuid import uuid4

logger = logging.getLogger(__name__)


def generate_dmca_packet(discovery: dict, scores: dict) -> tuple[bytes, str]:
    """
    Generate a legal-grade DMCA takedown PDF with:
      - Evidence of Original Ownership (blockchain TX, upload timestamp, filename)
      - Fingerprint Match Evidence (similarity bar, morph sub-score table)
      - Legal Declaration boilerplate
      - QR code linking to the infringing URL
    Saves to S3 at  dmca-packets/{asset_id}/{uuid}.pdf
    Returns (pdf_bytes, s3_url).
    """
    from reportlab.lib.pagesizes import letter
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.platypus import (
        SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
        HRFlowable, Image as RLImage,
    )
    import qrcode
    import boto3
    from botocore.exceptions import BotoCoreError, ClientError

    # ── helpers ──────────────────────────────────────────────────────────────

    def _similarity_bar(similarity: float, width: int = 20) -> str:
        """Return a unicode block-bar string, e.g. ████████░░ 82%"""
        pct = min(max(similarity, 0.0), 1.0)
        filled = round(pct * width)
        bar = "█" * filled + "░" * (width - filled)
        return f"{bar}  {pct * 100:.1f}%"

    def _qr_image_flowable(url: str, size: float = 1.4 * inch) -> RLImage:
        """Generate a QR code for *url* and return a ReportLab Image flowable."""
        qr = qrcode.QRCode(
            version=None,
            error_correction=qrcode.constants.ERROR_CORRECT_M,
            box_size=6,
            border=2,
        )
        qr.add_data(url)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        buf.seek(0)
        rl_img = RLImage(buf, width=size, height=size)
        return rl_img

    # ── document setup ────────────────────────────────────────────────────────

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        leftMargin=0.85 * inch,
        rightMargin=0.85 * inch,
        topMargin=0.9 * inch,
        bottomMargin=0.9 * inch,
    )

    styles = getSampleStyleSheet()
    W = letter[0] - 1.7 * inch  # usable text width

    # custom styles
    section_style = ParagraphStyle(
        "SectionHeader",
        parent=styles["Heading2"],
        textColor=colors.HexColor("#1a1a2e"),
        spaceBefore=14,
        spaceAfter=4,
        borderPad=4,
    )
    mono_style = ParagraphStyle(
        "Mono",
        parent=styles["Normal"],
        fontName="Courier",
        fontSize=8,
        leading=11,
    )
    label_style = ParagraphStyle(
        "Label",
        parent=styles["Normal"],
        fontSize=9,
        textColor=colors.HexColor("#555555"),
    )
    declaration_style = ParagraphStyle(
        "Declaration",
        parent=styles["Normal"],
        fontSize=9,
        leading=14,
        textColor=colors.HexColor("#222222"),
    )

    # header accent colour
    ACCENT = colors.HexColor("#c0392b")  # deep red – legal / urgent

    def _hr():
        return HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#cccccc"),
                          spaceAfter=6, spaceBefore=2)

    def _section(title: str):
        story.append(Spacer(1, 6))
        story.append(Paragraph(title, section_style))
        story.append(_hr())

    # ── data extraction ───────────────────────────────────────────────────────

    asset_id          = discovery.get("matched_asset_id", "UNKNOWN")
    infringing_url    = discovery.get("url", "")
    platform          = discovery.get("platform", "unknown")
    account_id        = discovery.get("account_id", "N/A")
    cosine_sim        = discovery.get("cosine_similarity", 0.0)
    blockchain_tx     = discovery.get("blockchain_tx_hash", "N/A")
    original_ts       = discovery.get("original_upload_timestamp", datetime.utcnow().isoformat())
    original_filename = discovery.get("original_filename", "N/A")

    morph_score  = scores.get("morph_score", 0.0)
    gan_score    = scores.get("gan_score", 0.0)
    freq_score   = scores.get("freq_score", 0.0)
    temp_score   = scores.get("temporal_score", 0.0)

    generated_at = datetime.utcnow().isoformat() + " UTC"

    # ── story ─────────────────────────────────────────────────────────────────

    story = []

    # ── Title block ───────────────────────────────────────────────────────────
    title_style = ParagraphStyle(
        "BigTitle",
        parent=styles["Title"],
        textColor=ACCENT,
        fontSize=18,
        spaceAfter=4,
    )
    story.append(Paragraph("DMCA TAKEDOWN NOTICE", title_style))
    story.append(Paragraph(
        f"<font color='#888888' size='9'>Generated: {generated_at} &nbsp;|&nbsp; "
        f"Asset: {asset_id}</font>",
        styles["Normal"],
    ))
    story.append(_hr())
    story.append(Spacer(1, 4))

    # ── Summary table ─────────────────────────────────────────────────────────
    summary_data = [
        ["Infringing URL", infringing_url],
        ["Platform",       platform],
        ["Account ID",     account_id],
        ["Notice Date",    generated_at],
    ]
    sum_table = Table(summary_data, colWidths=[130, W - 130])
    sum_table.setStyle(TableStyle([
        ("FONTNAME",    (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTSIZE",    (0, 0), (-1, -1), 9),
        ("TEXTCOLOR",   (0, 0), (0, -1), colors.HexColor("#333333")),
        ("ROWBACKGROUNDS", (0, 0), (-1, -1),
         [colors.HexColor("#f9f9f9"), colors.white]),
        ("GRID",        (0, 0), (-1, -1), 0.4, colors.HexColor("#dddddd")),
        ("LEFTPADDING",  (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING",   (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING",(0, 0), (-1, -1), 4),
    ]))
    story.append(sum_table)

    # ── 1. Evidence of Original Ownership ────────────────────────────────────
    _section("1. Evidence of Original Ownership")

    # Blockchain TX as clickable hyperlink
    if blockchain_tx and blockchain_tx != "N/A":
        # Prefer Etherscan for 0x… hashes, else OpenTimestamps
        if blockchain_tx.startswith("0x"):
            tx_url = f"https://etherscan.io/tx/{blockchain_tx}"
            tx_label = "Etherscan"
        else:
            tx_url = f"https://opentimestamps.org/timestamp/{blockchain_tx}"
            tx_label = "OpenTimestamps"
        tx_link = (
            f'Blockchain TX Hash: <link href="{tx_url}" color="blue">'
            f'<u>{blockchain_tx}</u></link> ({tx_label})'
        )
    else:
        tx_link = "Blockchain TX Hash: N/A"

    ownership_data = [
        ["Blockchain Proof",     Paragraph(tx_link, styles["Normal"])],
        ["Original Upload Time", Paragraph(original_ts, mono_style)],
        ["Original Filename",    Paragraph(original_filename, styles["Normal"])],
        ["Asset ID",             Paragraph(asset_id, mono_style)],
    ]
    own_table = Table(ownership_data, colWidths=[160, W - 160])
    own_table.setStyle(TableStyle([
        ("FONTNAME",     (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTSIZE",     (0, 0), (-1, -1), 9),
        ("ROWBACKGROUNDS", (0, 0), (-1, -1),
         [colors.HexColor("#fff8f8"), colors.white]),
        ("GRID",         (0, 0), (-1, -1), 0.4, colors.HexColor("#dddddd")),
        ("VALIGN",       (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING",  (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING",   (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING",(0, 0), (-1, -1), 5),
    ]))
    story.append(own_table)

    # ── 2. Fingerprint Match Evidence ─────────────────────────────────────────
    _section("2. Fingerprint Match Evidence")

    # Visual similarity bar
    bar_text = _similarity_bar(cosine_sim)
    story.append(Paragraph(
        f"<b>Cosine Similarity:</b>  <font name='Courier'>{bar_text}</font>",
        styles["Normal"],
    ))
    story.append(Spacer(1, 8))

    # Morph sub-score table
    def _score_colour(s: float) -> str:
        if s >= 75:
            return "#c0392b"   # red   – high risk
        if s >= 50:
            return "#e67e22"   # amber – medium
        return "#27ae60"       # green – low

    sub_headers = [
        Paragraph("<b>Sub-Score</b>", styles["Normal"]),
        Paragraph("<b>Value</b>",     styles["Normal"]),
        Paragraph("<b>Risk Level</b>", styles["Normal"]),
        Paragraph("<b>Visual Bar</b>", styles["Normal"]),
    ]
    sub_rows = [
        ("GAN Artifact Score",    gan_score),
        ("Frequency Analysis",    freq_score),
        ("Temporal Consistency",  temp_score),
        ("Overall Morph Score",   morph_score),
    ]
    sub_data = [sub_headers]
    for label, val in sub_rows:
        risk = "HIGH" if val >= 75 else ("MEDIUM" if val >= 50 else "LOW")
        col  = _score_colour(val)
        sub_data.append([
            Paragraph(label, styles["Normal"]),
            Paragraph(f"<b><font color='{col}'>{val:.1f}</font></b>", styles["Normal"]),
            Paragraph(f"<font color='{col}'><b>{risk}</b></font>", styles["Normal"]),
            Paragraph(f"<font name='Courier'>{_similarity_bar(val / 100, 12)}</font>",
                      styles["Normal"]),
        ])

    sub_table = Table(sub_data, colWidths=[160, 55, 65, W - 280])
    sub_table.setStyle(TableStyle([
        ("BACKGROUND",   (0, 0), (-1, 0),  colors.HexColor("#1a1a2e")),
        ("TEXTCOLOR",    (0, 0), (-1, 0),  colors.white),
        ("FONTNAME",     (0, 0), (-1, 0),  "Helvetica-Bold"),
        ("FONTSIZE",     (0, 0), (-1, -1), 9),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1),
         [colors.HexColor("#fafafa"), colors.white]),
        ("GRID",         (0, 0), (-1, -1), 0.4, colors.HexColor("#cccccc")),
        ("VALIGN",       (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING",  (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING",   (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING",(0, 0), (-1, -1), 4),
        # Highlight overall score row
        ("BACKGROUND",   (0, 4), (-1, 4),  colors.HexColor("#fdf3f3")),
        ("FONTNAME",     (0, 4), (-1, 4),  "Helvetica-Bold"),
    ]))
    story.append(sub_table)

    # ── 3. QR Code (infringing URL) ───────────────────────────────────────────
    _section("3. Infringing Content — QR Code")

    if infringing_url:
        qr_img = _qr_image_flowable(infringing_url, size=1.3 * inch)
        qr_table = Table(
            [[qr_img,
              Paragraph(
                  f"<b>Scan to view infringing content</b><br/><br/>"
                  f'<link href="{infringing_url}" color="blue"><u>{infringing_url}</u></link>',
                  styles["Normal"],
              )]],
            colWidths=[1.6 * inch, W - 1.6 * inch],
        )
        qr_table.setStyle(TableStyle([
            ("VALIGN",  (0, 0), (-1, -1), "MIDDLE"),
            ("LEFTPADDING",  (0, 0), (-1, -1), 6),
        ]))
        story.append(qr_table)
    else:
        story.append(Paragraph("No infringing URL provided.", label_style))

    # ── 4. Legal Declaration ──────────────────────────────────────────────────
    _section("4. Legal Declaration")

    good_faith = (
        "I have a good faith belief that use of the copyrighted materials described above "
        "as allegedly infringing is not authorized by the copyright owner, its agent, or the law. "
        "The information in this notification is accurate, and I swear, under penalty of perjury, "
        "that I am the owner, or an agent authorized to act on behalf of the owner, of an "
        "exclusive right that is allegedly infringed.\n\n"
        "This notice is sent pursuant to the Digital Millennium Copyright Act (DMCA), "
        "17 U.S.C. § 512(c)(3), and analogous provisions of applicable international law. "
        "The copyright owner reserves all rights and remedies available under applicable law."
    )
    for para in good_faith.split("\n\n"):
        story.append(Paragraph(para, declaration_style))
        story.append(Spacer(1, 6))

    story.append(Spacer(1, 16))

    # Signature block
    sig_data = [
        ["Authorized Signatory:", "________________________________"],
        ["Printed Name:",         "________________________________"],
        ["Title / Role:",         "________________________________"],
        ["Date:",                 "________________________________"],
        ["Electronic Signature:", "________________________________"],
    ]
    sig_table = Table(sig_data, colWidths=[150, W - 150])
    sig_table.setStyle(TableStyle([
        ("FONTNAME",     (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTSIZE",     (0, 0), (-1, -1), 9),
        ("BOTTOMPADDING",(0, 0), (-1, -1), 10),
        ("LINEBELOW",    (1, 0), (1, -1), 0.5, colors.black),
    ]))
    story.append(sig_table)

    # ── Build PDF ─────────────────────────────────────────────────────────────
    doc.build(story)
    pdf_bytes = buffer.getvalue()

    # ── Upload to S3 ──────────────────────────────────────────────────────────
    s3_key    = f"dmca-packets/{asset_id}/{uuid4()}.pdf"
    s3_bucket = os.getenv("DMCA_S3_BUCKET", "your-dmca-bucket")
    s3_url    = f"https://{s3_bucket}.s3.amazonaws.com/{s3_key}"

    try:
        s3 = boto3.client(
            "s3",
            aws_access_key_id     = os.getenv("AWS_ACCESS_KEY_ID"),
            aws_secret_access_key = os.getenv("AWS_SECRET_ACCESS_KEY"),
            region_name           = os.getenv("AWS_REGION", "us-east-1"),
        )
        s3.put_object(
            Bucket      = s3_bucket,
            Key         = s3_key,
            Body        = pdf_bytes,
            ContentType = "application/pdf",
            Metadata    = {
                "asset-id":      asset_id,
                "platform":      platform,
                "generated-at":  datetime.utcnow().isoformat(),
            },
        )
        logger.info(f"DMCA packet uploaded → s3://{s3_bucket}/{s3_key}")
    except (BotoCoreError, ClientError) as exc:
        logger.error(f"S3 upload failed: {exc}")
        # Return a local fallback path so calling code can retry
        s3_url = f"s3://{s3_bucket}/{s3_key}  [UPLOAD FAILED: {exc}]"

    return pdf_bytes, s3_url


# ── Quick smoke-test (run this file directly) ─────────────────────────────────
if __name__ == "__main__":
    import sys

    sample_discovery = {
        "matched_asset_id":         "asset_abc123",
        "url":                      "https://example-platform.com/videos/xyz987",
        "platform":                 "example_platform",
        "account_id":               "acc_hostile_42",
        "cosine_similarity":        0.91,
        "blockchain_tx_hash":       "0xdeadbeef1234567890abcdef1234567890abcdef1234567890abcdef12345678",
        "original_upload_timestamp": "2024-11-01T08:30:00Z",
        "original_filename":        "my_original_video_4k.mp4",
    }
    sample_scores = {
        "morph_score":    82.5,
        "gan_score":      74.0,
        "freq_score":     55.3,
        "temporal_score": 91.2,
    }

    pdf_bytes, s3_url = generate_dmca_packet(sample_discovery, sample_scores)

    out_path = "/mnt/user-data/outputs/dmca_sample.pdf"
    with open(out_path, "wb") as f:
        f.write(pdf_bytes)

    print(f"PDF saved  → {out_path}  ({len(pdf_bytes):,} bytes)")
    print(f"S3 URL     → {s3_url}")
    sys.exit(0)
