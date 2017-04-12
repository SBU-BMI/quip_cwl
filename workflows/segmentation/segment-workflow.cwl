class: Workflow
cwlVersion: v1.0
inputs:
- id: user
  type: string
- id: case_id
  type: string
outputs:
  fileout:
    outputSource: segment_curation/output_log
    type: File
steps:
  segment_curation:
    in:
      user: user
      case_id: case_id      
    out:
    - output_log
    run: segment_curation.yaml
