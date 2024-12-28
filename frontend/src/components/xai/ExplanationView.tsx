import React, { useEffect, useRef } from 'react';
import * as d3 from 'd3';
import { Explanation, VisualizationData } from '../../types/xai';

interface ExplanationViewProps {
  explanation: Explanation;
  onVisualizationClick?: (data: any) => void;
  className?: string;
}

const ExplanationView: React.FC<ExplanationViewProps> = ({
  explanation,
  onVisualizationClick,
  className = ''
}) => {
  const treeRef = useRef<SVGSVGElement>(null);
  const sankeyRef = useRef<SVGSVGElement>(null);
  const networkRef = useRef<SVGSVGElement>(null);
  const metricsRef = useRef<SVGSVGElement>(null);

  useEffect(() => {
    if (explanation.visualization_data) {
      renderVisualizations(explanation.visualization_data);
    }
  }, [explanation]);

  const renderVisualizations = (visualData: VisualizationData) => {
    if (visualData.reasoning_flow) {
      renderDecisionTree(visualData.reasoning_flow);
    }
    if (visualData.compliance_status) {
      renderSankeyDiagram(visualData.compliance_status);
    }
    if (visualData.evidence_network) {
      renderEvidenceNetwork(visualData.evidence_network);
    }
    if (visualData.confidence_metrics) {
      renderMetricsVisualization(visualData.confidence_metrics);
    }
  };

  const renderDecisionTree = (data: any) => {
    if (!treeRef.current) return;

    const width = 800;
    const height = 600;
    const margin = { top: 20, right: 90, bottom: 30, left: 90 };

    const svg = d3.select(treeRef.current)
      .attr('width', width)
      .attr('height', height);

    // Clear previous content
    svg.selectAll('*').remove();

    const g = svg.append('g')
      .attr('transform', `translate(${margin.left},${margin.top})`);

    // Create tree layout
    const treeLayout = d3.tree()
      .size([height - margin.top - margin.bottom, width - margin.left - margin.right]);

    // Create root node
    const root = d3.hierarchy(data);
    const treeData = treeLayout(root);

    // Add links
    const link = g.selectAll('.link')
      .data(treeData.links())
      .enter().append('path')
      .attr('class', 'link')
      .attr('d', d3.linkHorizontal()
        .x((d: any) => d.y)
        .y((d: any) => d.x));

    // Add nodes
    const node = g.selectAll('.node')
      .data(treeData.descendants())
      .enter().append('g')
      .attr('class', 'node')
      .attr('transform', (d: any) => `translate(${d.y},${d.x})`);

    // Add node circles
    node.append('circle')
      .attr('r', 10)
      .style('fill', (d: any) => d.data.confidence >= 0.7 ? '#2ca02c' : '#d62728');

    // Add node labels
    node.append('text')
      .attr('dy', '.35em')
      .attr('x', (d: any) => d.children ? -13 : 13)
      .style('text-anchor', (d: any) => d.children ? 'end' : 'start')
      .text((d: any) => d.data.label);
  };

  const renderSankeyDiagram = (data: any) => {
    if (!sankeyRef.current) return;

    const width = 800;
    const height = 400;
    const margin = { top: 20, right: 20, bottom: 20, left: 20 };

    const svg = d3.select(sankeyRef.current)
      .attr('width', width)
      .attr('height', height);

    // Clear previous content
    svg.selectAll('*').remove();

    const g = svg.append('g')
      .attr('transform', `translate(${margin.left},${margin.top})`);

    // Create Sankey layout
    const sankey = d3.sankey()
      .nodeWidth(15)
      .nodePadding(10)
      .extent([[0, 0], [width - margin.left - margin.right, height - margin.top - margin.bottom]]);

    // Generate Sankey data
    const { nodes, links } = sankey(data);

    // Add links
    const link = g.selectAll('.link')
      .data(links)
      .enter().append('path')
      .attr('class', 'link')
      .attr('d', d3.sankeyLinkHorizontal())
      .style('stroke-width', (d: any) => Math.max(1, d.width));

    // Add nodes
    const node = g.selectAll('.node')
      .data(nodes)
      .enter().append('g')
      .attr('class', 'node')
      .attr('transform', (d: any) => `translate(${d.x0},${d.y0})`);

    // Add node rectangles
    node.append('rect')
      .attr('height', (d: any) => d.y1 - d.y0)
      .attr('width', sankey.nodeWidth())
      .style('fill', (d: any) => d.color);

    // Add node labels
    node.append('text')
      .attr('x', -6)
      .attr('y', (d: any) => (d.y1 - d.y0) / 2)
      .attr('dy', '.35em')
      .attr('text-anchor', 'end')
      .text((d: any) => d.name);
  };

  const renderEvidenceNetwork = (data: any) => {
    if (!networkRef.current) return;

    const width = 800;
    const height = 600;

    const svg = d3.select(networkRef.current)
      .attr('width', width)
      .attr('height', height);

    // Clear previous content
    svg.selectAll('*').remove();

    // Create force simulation
    const simulation = d3.forceSimulation(data.nodes)
      .force('link', d3.forceLink(data.links).id((d: any) => d.id))
      .force('charge', d3.forceManyBody())
      .force('center', d3.forceCenter(width / 2, height / 2));

    // Add links
    const link = svg.append('g')
      .selectAll('line')
      .data(data.links)
      .enter().append('line')
      .style('stroke', '#999')
      .style('stroke-opacity', 0.6);

    // Add nodes
    const node = svg.append('g')
      .selectAll('circle')
      .data(data.nodes)
      .enter().append('circle')
      .attr('r', 5)
      .style('fill', (d: any) => d.color)
      .call(d3.drag()
        .on('start', dragstarted)
        .on('drag', dragged)
        .on('end', dragended));

    // Add node labels
    const label = svg.append('g')
      .selectAll('text')
      .data(data.nodes)
      .enter().append('text')
      .text((d: any) => d.label)
      .style('font-size', '12px')
      .style('font-family', 'Arial')
      .attr('dx', 12)
      .attr('dy', 4);

    // Update positions on simulation tick
    simulation.on('tick', () => {
      link
        .attr('x1', (d: any) => d.source.x)
        .attr('y1', (d: any) => d.source.y)
        .attr('x2', (d: any) => d.target.x)
        .attr('y2', (d: any) => d.target.y);

      node
        .attr('cx', (d: any) => d.x)
        .attr('cy', (d: any) => d.y);

      label
        .attr('x', (d: any) => d.x)
        .attr('y', (d: any) => d.y);
    });

    // Drag functions
    function dragstarted(event: any) {
      if (!event.active) simulation.alphaTarget(0.3).restart();
      event.subject.fx = event.subject.x;
      event.subject.fy = event.subject.y;
    }

    function dragged(event: any) {
      event.subject.fx = event.x;
      event.subject.fy = event.y;
    }

    function dragended(event: any) {
      if (!event.active) simulation.alphaTarget(0);
      event.subject.fx = null;
      event.subject.fy = null;
    }
  };

  const renderMetricsVisualization = (data: any) => {
    if (!metricsRef.current) return;

    const width = 400;
    const height = 400;
    const margin = { top: 20, right: 20, bottom: 30, left: 40 };
    const radius = Math.min(width, height) / 2 - margin.top;

    const svg = d3.select(metricsRef.current)
      .attr('width', width)
      .attr('height', height);

    // Clear previous content
    svg.selectAll('*').remove();

    const g = svg.append('g')
      .attr('transform', `translate(${width / 2},${height / 2})`);

    // Create pie layout
    const pie = d3.pie()
      .value((d: any) => d.value)
      .sort(null);

    // Create arc generator
    const arc = d3.arc()
      .innerRadius(radius * 0.6)
      .outerRadius(radius);

    // Create arcs
    const arcs = g.selectAll('.arc')
      .data(pie(data))
      .enter().append('g')
      .attr('class', 'arc');

    // Add paths
    arcs.append('path')
      .attr('d', arc as any)
      .style('fill', (d: any) => d.data.color);

    // Add labels
    arcs.append('text')
      .attr('transform', (d: any) => `translate(${arc.centroid(d)})`)
      .attr('dy', '.35em')
      .style('text-anchor', 'middle')
      .text((d: any) => `${d.data.label}: ${(d.data.value * 100).toFixed(1)}%`);
  };

  return (
    <div className={`explanation-view ${className}`}>
      <div className="explanation-summary">
        <h3>Decision Explanation</h3>
        <p>{explanation.summary}</p>
      </div>

      <div className="visualization-container">
        <div className="visualization-section">
          <h4>Decision Process</h4>
          <svg ref={treeRef} className="decision-tree" />
        </div>

        <div className="visualization-section">
          <h4>Information Flow</h4>
          <svg ref={sankeyRef} className="sankey-diagram" />
        </div>

        <div className="visualization-section">
          <h4>Evidence Network</h4>
          <svg ref={networkRef} className="evidence-network" />
        </div>

        <div className="visualization-section">
          <h4>Confidence Metrics</h4>
          <svg ref={metricsRef} className="metrics-visualization" />
        </div>
      </div>

      <div className="explanation-components">
        {explanation.components.map((component, index) => (
          <div key={index} className="component-card">
            <h4>{component.component_type}</h4>
            <p>{component.description}</p>
            <div className="confidence-bar">
              <div
                className="confidence-fill"
                style={{
                  width: `${component.importance_score * 100}%`,
                  backgroundColor: component.importance_score >= 0.7 ? '#2ca02c' : '#d62728'
                }}
              />
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default ExplanationView; 