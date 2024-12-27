# Document Validation Criteria

## Document Validation

### 1. Metadata Validation
- **Required Fields**
  - Title
  - Document ID
  - Source
  - Publication Date
  - Document Type
  - Version

- **Format Requirements**
  - Dates in ISO 8601
  - IDs following system convention
  - URLs properly formatted
  - Enumerated types match defined values

- **Consistency Checks**
  - Publication date ≤ current date
  - Version numbers sequential
  - Status transitions valid
  - Cross-reference integrity

### 2. Content Validation

- **Structural Requirements**
  - Valid XML/HTML structure
  - Required sections present
  - Proper nesting of elements
  - Complete table structures
  - Valid list formatting

- **Text Quality**
  - No broken character encoding
  - Proper paragraph separation
  - Consistent formatting
  - No duplicate content
  - Readable text blocks

- **Reference Integrity**
  - Valid internal references
  - Accessible external links
  - Correct citation formats
  - Resolvable cross-references
  - Valid policy references

## Relationship Validation

### 1. Graph Structure
- **Node Requirements**
  - Unique identifiers
  - Required properties present
  - Valid property types
  - No orphaned nodes
  - Proper labels

- **Edge Requirements**
  - Valid relationship types
  - Required edge properties
  - Directional correctness
  - No self-loops (unless allowed)
  - Proper edge weights

### 2. Semantic Validation
- **Relationship Logic**
  - Valid source/target combinations
  - Temporal consistency
  - Hierarchical validity
  - Domain rules compliance
  - Relationship constraints

## Policy Compliance

### 1. Document Requirements
- **Classification Rules**
  - Proper security levels
  - Required classifications
  - Access control markers
  - Distribution statements
  - Handling instructions

- **Content Rules**
  - Required disclaimers
  - Mandatory sections
  - Format compliance
  - Review status
  - Approval signatures

### 2. Process Requirements
- **Workflow Validation**
  - Required approvals
  - Review completion
  - Version control
  - Audit trail
  - Change tracking

## Quality Metrics

### 1. Content Quality
```json
{
  "metrics": {
    "completeness": {
      "required_fields": 1.0,
      "optional_fields": 0.8,
      "content_sections": 0.95
    },
    "accuracy": {
      "spelling": 0.99,
      "grammar": 0.98,
      "formatting": 1.0
    },
    "consistency": {
      "style": 0.95,
      "terminology": 0.90,
      "references": 1.0
    }
  }
}
```

### 2. Relationship Quality
```json
{
  "metrics": {
    "connectivity": {
      "internal_refs": 1.0,
      "external_refs": 0.95,
      "bidirectional": 0.90
    },
    "accuracy": {
      "relationship_types": 0.98,
      "property_values": 0.95,
      "temporal_order": 1.0
    }
  }
}
```

## Validation Process

### 1. Pre-ingestion
- Source verification
- Format validation
- Size limits
- Content type check
- Basic structure validation

### 2. During Processing
- Content extraction validation
- Transformation verification
- Relationship building checks
- Policy compliance checks
- Quality metrics calculation

### 3. Post-processing
- Final schema validation
- Relationship integrity
- Storage confirmation
- Index updates
- Audit trail verification

## Error Categories

### 1. Critical Errors
- Missing required fields
- Invalid document structure
- Broken relationships
- Policy violations
- Data corruption

### 2. Warnings
- Missing optional fields
- Low quality metrics
- Weak relationships
- Performance issues
- Minor inconsistencies

## Validation Response

### 1. Success Response
```json
{
  "status": "valid",
  "document_id": "doc123",
  "timestamp": "2024-01-20T10:30:00Z",
  "metrics": {
    "quality_score": 0.95,
    "relationship_score": 0.92,
    "compliance_score": 1.0
  }
}
```

### 2. Error Response
```json
{
  "status": "invalid",
  "document_id": "doc123",
  "timestamp": "2024-01-20T10:30:00Z",
  "errors": [
    {
      "code": "ERR001",
      "field": "publication_date",
      "message": "Invalid date format",
      "severity": "critical"
    }
  ],
  "warnings": [
    {
      "code": "WARN001",
      "field": "references",
      "message": "Unresolved external reference",
      "severity": "warning"
    }
  ]
}
``` 