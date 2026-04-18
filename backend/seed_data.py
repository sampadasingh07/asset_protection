#!/usr/bin/env python
"""Seed initial demo data for VeriLens"""

from app.database import get_db, init_db
from app.models import Asset, User, Violation, EnforcementRecord
from app.models.user import Organisation
from sqlalchemy.orm import Session
import json

def seed_data():
    """Create initial demo organization, user, and assets"""
    init_db()
    
    db_gen = get_db()
    db = next(db_gen)
    
    try:
        # Create demo organization
        from app.models.base import generate_uuid
        org_id = generate_uuid()
        org = Organisation(
            id=org_id,
            name="Demo Organisation",
            slug="demo-org"
        )
        db.add(org)
        db.flush()
        
        # Create demo user
        from app.security import hash_password
        user_id = generate_uuid()
        user = User(
            id=user_id,
            organisation_id=org_id,
            email="admin@demo.org",
            full_name="Admin User",
            password_hash=hash_password("demo123"),
            role="admin"
        )
        db.add(user)
        db.flush()
        
        # Create demo assets
        asset1_id = generate_uuid()
        asset1 = Asset(
            id=asset1_id,
            organisation_id=org_id,
            owner_user_id=user_id,
            title="Sample Protected Video",
            file_name="sample_video.mp4",
            file_path="uploads/sample_video.mp4",
            content_type="video/mp4",
            source_url="https://example.com/video",
            status="ready",
            fingerprint_vector=[0.1, 0.2, 0.3, 0.4, 0.5]
        )
        db.add(asset1)
        db.flush()
        
        # Create demo violation
        violation = Violation(
            id=generate_uuid(),
            organisation_id=org_id,
            asset_id=asset1_id,
            match_id=None,
            severity="high",
            status="open",
            confidence=0.95,
            summary="Asset detected on unauthorized platform",
            source_url="https://infringing-site.com/stolen-video"
        )
        db.add(violation)
        db.flush()
        
        # Create enforcement record
        enforcement = EnforcementRecord(
            id=generate_uuid(),
            violation_id=violation.id,
            action_type="DMCA_TAKEDOWN",
            platform_name="YouTube",
            status="pending",
            external_reference="DMCA-2026-001",
            notes="Automated takedown initiated"
        )
        db.add(enforcement)
        
        db.commit()
        print("✓ Demo data seeded successfully!")
        print(f"  Org ID: {org_id}")
        print(f"  User: admin@demo.org (password: demo123)")
        print(f"  Assets: 1 created")
        print(f"  Violations: 1 created")
        
    except Exception as e:
        db.rollback()
        print(f"✗ Error seeding data: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    seed_data()
