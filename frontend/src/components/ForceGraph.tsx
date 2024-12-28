import React, { useEffect, useRef } from 'react';
import * as d3 from 'd3';
import { Document, Relationship } from '@/types';
import './ForceGraph.css';

interface ForceGraphProps {
  document: Document;
  relationships: Relationship[];
  onNodeClick: (nodeId: string) => void;
}

interface Node extends d3.SimulationNodeDatum {
  id: string;
  label: string;
  type: string;
  radius: number;
}

interface Link extends d3.SimulationLinkDatum<Node> {
  source: string | Node;
  target: string | Node;
  type: string;
}

export function ForceGraph({ document, relationships, onNodeClick }: ForceGraphProps) {
  const svgRef = useRef<SVGSVGElement>(null);

  useEffect(() => {
    if (!svgRef.current || !document || !relationships) return;

    // Clear previous graph
    d3.select(svgRef.current).selectAll('*').remove();

    // Prepare data
    const nodes: Node[] = [
      {
        id: document.document_id,
        label: document.title,
        type: 'current',
        radius: 20,
      },
      ...relationships.flatMap(rel => [
        {
          id: rel.source_id,
          label: rel.source_title,
          type: 'related',
          radius: 15,
        },
        {
          id: rel.target_id,
          label: rel.target_title,
          type: 'related',
          radius: 15,
        },
      ]).filter(node => node.id !== document.document_id),
    ];

    const links: Link[] = relationships.map(rel => ({
      source: rel.source_id,
      target: rel.target_id,
      type: rel.relationship_type,
    }));

    // Set up SVG
    const width = svgRef.current.clientWidth;
    const height = svgRef.current.clientHeight;
    const svg = d3.select(svgRef.current)
      .attr('width', width)
      .attr('height', height);

    // Create simulation
    const simulation = d3.forceSimulation<Node>(nodes)
      .force('link', d3.forceLink<Node, Link>(links)
        .id(d => d.id)
        .distance(100))
      .force('charge', d3.forceManyBody().strength(-200))
      .force('center', d3.forceCenter(width / 2, height / 2))
      .force('collision', d3.forceCollide().radius(d => ((d as Node).radius || 0) + 10));

    // Create arrow marker
    svg.append('defs').selectAll('marker')
      .data(['arrow'])
      .join('marker')
      .attr('id', d => d)
      .attr('viewBox', '0 -5 10 10')
      .attr('refX', 25)
      .attr('refY', 0)
      .attr('markerWidth', 6)
      .attr('markerHeight', 6)
      .attr('orient', 'auto')
      .append('path')
      .attr('d', 'M0,-5L10,0L0,5')
      .attr('fill', '#999');

    // Create links
    const link = svg.append('g')
      .selectAll('line')
      .data(links)
      .join('line')
      .attr('stroke', '#999')
      .attr('stroke-opacity', 0.6)
      .attr('stroke-width', 1)
      .attr('marker-end', 'url(#arrow)');

    // Create nodes
    const node = svg.append('g')
      .selectAll<SVGGElement, Node>('g')
      .data(nodes)
      .join('g')
      .call(d3.drag<SVGGElement, Node>()
        .on('start', dragstarted)
        .on('drag', dragged)
        .on('end', dragended)
      )
      .on('click', (event, d) => onNodeClick(d.id));

    // Add circles to nodes
    node.append('circle')
      .attr('r', d => d.radius)
      .attr('fill', d => d.type === 'current' ? '#3b82f6' : '#60a5fa')
      .attr('stroke', '#1d4ed8')
      .attr('stroke-width', 1.5);

    // Add labels to nodes
    node.append('text')
      .text(d => d.label)
      .attr('x', d => d.radius + 5)
      .attr('y', '0.31em')
      .attr('font-size', '12px')
      .attr('fill', '#374151');

    // Update positions on tick
    simulation.on('tick', () => {
      link
        .attr('x1', d => (d.source as Node).x!)
        .attr('y1', d => (d.source as Node).y!)
        .attr('x2', d => (d.target as Node).x!)
        .attr('y2', d => (d.target as Node).y!);

      node
        .attr('transform', d => `translate(${d.x},${d.y})`);
    });

    // Drag functions
    function dragstarted(event: d3.D3DragEvent<SVGGElement, Node, Node>) {
      if (!event.active) simulation.alphaTarget(0.3).restart();
      event.subject.fx = event.subject.x;
      event.subject.fy = event.subject.y;
    }

    function dragged(event: d3.D3DragEvent<SVGGElement, Node, Node>) {
      event.subject.fx = event.x;
      event.subject.fy = event.y;
    }

    function dragended(event: d3.D3DragEvent<SVGGElement, Node, Node>) {
      if (!event.active) simulation.alphaTarget(0);
      event.subject.fx = null;
      event.subject.fy = null;
    }

    // Cleanup
    return () => {
      simulation.stop();
    };
  }, [document, relationships, onNodeClick]);

  return (
    <svg
      ref={svgRef}
      className="w-full h-full force-graph-container"
    />
  );
} 