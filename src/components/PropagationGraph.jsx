/* ═══════════════════════════════════════════════════════════════════════
   PropagationGraph — D3.js force-directed graph visualization
   Module 4A from GDG spec
   ═══════════════════════════════════════════════════════════════════════ */

import { useEffect, useRef, useCallback } from 'react';
import * as d3 from 'd3';

const COLORS = {
  account: '#FFFFFF',
  url_low: '#888888',
  url_medium: '#CCCCCC',
  url_high: '#FFFFFF',
  link_posted: '#888888',
  link_shared: '#AAAAAA',
};

function getMorphColor(score) {
  if (score > 70) return COLORS.url_high;
  if (score > 40) return COLORS.url_medium;
  return COLORS.url_low;
}

export default function PropagationGraph({ nodes, links, onNodeClick, height = 500 }) {
  const svgRef = useRef(null);
  const simulationRef = useRef(null);
  const containerRef = useRef(null);

  const renderGraph = useCallback(() => {
    if (!svgRef.current || !nodes || !nodes.length) return;

    const W = containerRef.current?.clientWidth || 800;
    const H = height;

    // Clear previous render
    d3.select(svgRef.current).selectAll('*').remove();

    const svg = d3
      .select(svgRef.current)
      .attr('width', W)
      .attr('height', H)
      .attr('viewBox', `0 0 ${W} ${H}`);

    // Deep copy nodes/links for D3 mutation
    const simNodes = nodes.map(d => ({ ...d }));
    const simLinks = links.map(d => ({ ...d }));

    // Defs: arrow markers + glow filter
    const defs = svg.append('defs');

    // Glow filter
    const filter = defs.append('filter').attr('id', 'glow');
    filter.append('feGaussianBlur').attr('stdDeviation', '3').attr('result', 'coloredBlur');
    const feMerge = filter.append('feMerge');
    feMerge.append('feMergeNode').attr('in', 'coloredBlur');
    feMerge.append('feMergeNode').attr('in', 'SourceGraphic');

    // Arrow markers
    ['posted', 'shared'].forEach((type) => {
      defs.append('marker')
        .attr('id', `arrow-${type}`)
        .attr('viewBox', '0 0 10 10')
        .attr('refX', 25)
        .attr('refY', 5)
        .attr('markerWidth', 6)
        .attr('markerHeight', 6)
        .attr('orient', 'auto-start-reverse')
        .append('path')
        .attr('d', 'M2 1L8 5L2 9')
        .attr('fill', 'none')
        .attr('stroke', type === 'posted' ? COLORS.link_posted : COLORS.link_shared)
        .attr('stroke-width', 1.5)
        .attr('stroke-linecap', 'round');
    });

    // Background grid
    const gridG = svg.append('g').attr('class', 'grid');
    for (let x = 0; x < W; x += 40) {
      gridG.append('line')
        .attr('x1', x).attr('y1', 0).attr('x2', x).attr('y2', H)
        .attr('stroke', 'rgba(255, 255, 255, 0.04)').attr('stroke-width', 0.5);
    }
    for (let y = 0; y < H; y += 40) {
      gridG.append('line')
        .attr('x1', 0).attr('y1', y).attr('x2', W).attr('y2', y)
        .attr('stroke', 'rgba(255, 255, 255, 0.04)').attr('stroke-width', 0.5);
    }

    // Zoom
    const g = svg.append('g');
    svg.call(
      d3.zoom()
        .scaleExtent([0.3, 3])
        .on('zoom', (event) => g.attr('transform', event.transform))
    );

    // Force simulation
    const simulation = d3
      .forceSimulation(simNodes)
      .force('link', d3.forceLink(simLinks).id(d => d.id).distance(140).strength(0.4))
      .force('charge', d3.forceManyBody().strength(-350))
      .force('center', d3.forceCenter(W / 2, H / 2))
      .force('collision', d3.forceCollide(35))
      .force('x', d3.forceX(W / 2).strength(0.05))
      .force('y', d3.forceY(H / 2).strength(0.05));

    simulationRef.current = simulation;

    // Links
    const link = g.append('g')
      .selectAll('line')
      .data(simLinks)
      .join('line')
      .attr('stroke', d => d.type === 'POSTED' ? COLORS.link_posted : COLORS.link_shared)
      .attr('stroke-width', d => d.type === 'SHARED_TO' ? 2 : 1.2)
      .attr('stroke-opacity', 0.5)
      .attr('stroke-dasharray', d => d.type === 'SHARED_TO' ? '6,4' : 'none')
      .attr('marker-end', d => `url(#arrow-${d.type === 'POSTED' ? 'posted' : 'shared'})`);

    // Node groups
    const node = g.append('g')
      .selectAll('g')
      .data(simNodes)
      .join('g')
      .attr('cursor', 'pointer')
      .on('click', (_, d) => onNodeClick?.(d))
      .call(
        d3.drag()
          .on('start', (event, d) => {
            if (!event.active) simulation.alphaTarget(0.3).restart();
            d.fx = d.x;
            d.fy = d.y;
          })
          .on('drag', (event, d) => {
            d.fx = event.x;
            d.fy = event.y;
          })
          .on('end', (event, d) => {
            if (!event.active) simulation.alphaTarget(0);
            d.fx = null;
            d.fy = null;
          })
      );

    // Outer glow ring for high-risk
    node.filter(d => d.type === 'url' && (d.morph_score || 0) > 70)
      .append('circle')
      .attr('r', 20)
      .attr('fill', 'none')
      .attr('stroke', COLORS.url_high)
      .attr('stroke-width', 1)
      .attr('stroke-opacity', 0.3)
      .style('filter', 'url(#glow)');

    // Main circles
    node.append('circle')
      .attr('r', d => d.type === 'account' ? 18 : 14)
      .attr('fill', d =>
        d.type === 'account'
          ? COLORS.account
          : getMorphColor(d.morph_score || 0)
      )
      .attr('stroke', 'rgba(234, 234, 255, 0.15)')
      .attr('stroke-width', 2)
      .attr('opacity', 0.9)
      .style('filter', d => (d.morph_score || 0) > 70 ? 'url(#glow)' : 'none')
      .on('mouseover', function() {
        d3.select(this).transition().duration(200).attr('r', d => d.type === 'account' ? 22 : 18);
      })
      .on('mouseout', function(_, d) {
        d3.select(this).transition().duration(200).attr('r', d.type === 'account' ? 18 : 14);
      });

    // Inner icon/label for nodes
    node.append('text')
      .text(d => {
        if (d.type === 'account') return d.id.slice(1, 4).toUpperCase();
        return d.morph_score ? Math.round(d.morph_score) : '?';
      })
      .attr('text-anchor', 'middle')
      .attr('dominant-baseline', 'central')
      .attr('font-size', d => d.type === 'account' ? 8 : 9)
      .attr('fill', 'white')
      .attr('font-weight', '600')
      .attr('font-family', 'Inter, sans-serif')
      .style('pointer-events', 'none');

    // Platform label below accounts
    node.filter(d => d.type === 'account' && d.platform)
      .append('text')
      .text(d => d.platform)
      .attr('text-anchor', 'middle')
      .attr('y', 30)
      .attr('font-size', 8)
      .attr('fill', '#9595C4')
      .attr('font-weight', '500')
      .attr('font-family', 'Inter, sans-serif')
      .style('pointer-events', 'none');

    // Account name below
    node.filter(d => d.type === 'account')
      .append('text')
      .text(d => d.id.length > 14 ? d.id.slice(0, 14) + '…' : d.id)
      .attr('text-anchor', 'middle')
      .attr('y', 42)
      .attr('font-size', 7)
      .attr('fill', '#888888')
      .attr('font-family', 'Inter, sans-serif')
      .style('pointer-events', 'none');

    // Tick update
    simulation.on('tick', () => {
      link
        .attr('x1', d => d.source.x)
        .attr('y1', d => d.source.y)
        .attr('x2', d => d.target.x)
        .attr('y2', d => d.target.y);
      node.attr('transform', d => `translate(${d.x},${d.y})`);
    });
  }, [nodes, links, onNodeClick, height]);

  useEffect(() => {
    renderGraph();
    return () => simulationRef.current?.stop();
  }, [renderGraph]);

  return (
    <div className="graph-container" ref={containerRef}>
      <div className="graph-header">
        <div className="card-title">
          <span style={{ color: 'var(--brand-primary-light)' }}>⬡</span>
          Viral Propagation Network
        </div>
        <div className="graph-legend">
          <div className="graph-legend-item">
            <span className="graph-legend-dot" style={{ background: COLORS.account }} />
            Account
          </div>
          <div className="graph-legend-item">
            <span className="graph-legend-dot" style={{ background: COLORS.url_high }} />
            High Risk
          </div>
          <div className="graph-legend-item">
            <span className="graph-legend-dot" style={{ background: COLORS.url_medium }} />
            Medium
          </div>
          <div className="graph-legend-item">
            <span className="graph-legend-dot" style={{ background: COLORS.url_low }} />
            Low
          </div>
          <div className="graph-legend-item">
            <span style={{
              width: '20px', height: '2px', display: 'inline-block',
              background: COLORS.link_posted, borderRadius: '1px'
            }} />
            Posted
          </div>
          <div className="graph-legend-item">
            <span style={{
              width: '20px', height: '2px', display: 'inline-block',
              borderTop: `2px dashed ${COLORS.link_shared}`,
            }} />
            Shared
          </div>
        </div>
      </div>
      <svg ref={svgRef} className="graph-svg" style={{ height: `${height}px` }} />
    </div>
  );
}

