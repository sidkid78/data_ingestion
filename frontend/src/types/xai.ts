/**
 * TypeScript types for XAI (Explainable AI) components
 */

export interface ExplanationComponent {
  component_type: 'reasoning' | 'compliance' | 'evidence' | 'counterfactual';
  description: string;
  importance_score: number;
  supporting_data: Record<string, any>;
  visualization_data?: Record<string, any>;
}

export interface ConfidenceMetrics {
  overall_confidence: number;
  reasoning_confidence: number;
  compliance_confidence: number;
  evidence_strength: number;
  [key: string]: number;
}

export interface VisualizationData {
  reasoning_flow?: {
    nodes: Array<{
      id: string;
      label: string;
      type: string;
      confidence: number;
      metadata?: Record<string, any>;
    }>;
    edges: Array<{
      source: string;
      target: string;
      weight: number;
    }>;
  };
  compliance_status?: {
    nodes: Array<{
      id: string;
      name: string;
      value: number;
      color: string;
    }>;
    links: Array<{
      source: number;
      target: number;
      value: number;
    }>;
  };
  evidence_network?: {
    nodes: Array<{
      id: string;
      label: string;
      type: string;
      weight: number;
      color: string;
    }>;
    links: Array<{
      source: string;
      target: string;
      weight: number;
    }>;
  };
  confidence_metrics?: Array<{
    label: string;
    value: number;
    color: string;
  }>;
}

export interface Explanation {
  summary: string;
  components: ExplanationComponent[];
  confidence_metrics: ConfidenceMetrics;
  visualization_data: VisualizationData;
  metadata: {
    explanation_type: string;
    target_audience: string;
    reasoning_type: string;
    timestamp: string;
    [key: string]: string;
  };
}

export interface ReasoningStep {
  description: string;
  type: string;
  confidence: number;
  metadata: Record<string, any>;
}

export interface ComplianceCheck {
  description: string;
  status: 'passed' | 'failed' | 'warning';
  confidence: number;
  details: string;
  metadata: Record<string, any>;
}

export interface EvidenceItem {
  description: string;
  type: string;
  confidence: number;
  source: string;
  metadata: Record<string, any>;
}

export interface CounterfactualScenario {
  description: string;
  conditions: string[];
  outcome: string;
  confidence: number;
  metadata: Record<string, any>;
}

export interface VisualizationConfig {
  type: 'tree' | 'sankey' | 'network' | 'metrics';
  options: {
    layout?: {
      orientation?: 'vertical' | 'horizontal';
      nodeSpacing?: number;
      levelSpacing?: number;
      nodeWidth?: number;
      nodePadding?: number;
      [key: string]: any;
    };
    annotations?: Array<{
      text: string;
      position: { x: number; y: number };
      style?: Record<string, any>;
    }>;
    [key: string]: any;
  };
  theme?: {
    colors: {
      primary: string;
      secondary: string;
      success: string;
      warning: string;
      neutral: string;
      [key: string]: string;
    };
    fonts: {
      family: string;
      size: {
        small: number;
        medium: number;
        large: number;
        [key: string]: number;
      };
    };
  };
  interactive: boolean;
} 