class: Workflow
cwlVersion: v1.0
inputs:
- id: user
  type: string
- id: case_id
  type: string
outputs:
  outputSource: segment_curation/output
  type: stdout
steps:
  segment_curation:
    in:
      user: user
      case_id: case_id      
    out:
    - output
    run: segment_curation.yaml
