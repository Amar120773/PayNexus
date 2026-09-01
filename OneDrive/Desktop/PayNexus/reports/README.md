# PayNexus Reports Index

This directory contains the documentation, research artifacts, and verification reports for the PayNexus Razorpay Buildathon project (powered by the MuleHunter detection engine).

For judges and reviewers, we recommend the following reading order to understand the problem, our approach, the technical architecture, and the empirical results.

## START HERE

1. [**Buildathon Story**](buildathon_story.md): The narrative of our journey, from identifying the problem to overcoming data leakage and achieving final results.
2. [**Novelty Statement**](novelty_statement.md): What makes MuleHunter different from traditional static fraud detection.
3. [**Final Metrics**](final_metrics.md): The **verified V2 results** on our held-out synthetic test set.
4. [**Razorpay Fit**](razorpay_fit.md): How MuleHunter aligns with Razorpay's ecosystem and solves a critical risk operations problem.

## TECHNICAL ARCHITECTURE

5. [**Final System Architecture**](final_system_architecture.md): The end-to-end design of the MuleHunter system, from data generation to inference.
6. [**Final Architecture Diagram Spec**](final_architecture_diagram_spec.md): Details of the system components and their interactions.

## RESEARCH RIGOR

7. [**Leakage Remediation**](leakage_remediation.md): Documentation of the structural leakage discovered in V1 and how we solved it using temporal network evolution in V2.
8. [**Final Hypothesis**](final_hypothesis.md): The core thesis tested by our ablation studies.
9. [**Phase 8 Verification**](phase8_verification.md): Verification of temporal safety and point-in-time inference constraints.

## DEMO

10. [**Final Demo Script**](final_demo_script.md): The step-by-step guide for presenting MuleHunter.
11. [**Demo Validation**](demo_validation.md): Health checks and verification of the demo scenarios.

> **Note**: Other files in this directory include historical research artifacts, ablation studies, and automated JSON/CSV exports. These are preserved for scientific integrity but the primary conclusions are summarized in the documents listed above.
