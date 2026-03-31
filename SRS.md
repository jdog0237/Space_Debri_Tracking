Software Requirements Specification
(SRS)
Project: Space Debris Tracking & Collision Risk Dashboard
Date: February 20, 2026
Prepared By: Ethan Bogart, Megan Botha, Jared Beaseley
Table of Contents

1. Introduction
   1.1 Purpose of the SRS
   1.2 Problem Statement
2. Overall System Description
3. Statement of Functional Requirements
4. Non-Functional Requirements
5. System Models and Diagrams
6. Design and Implementation Constraints
7. References and Sources of Information
8. Introduction
   1.1 Purpose of the SRS
   This document defines the functional and non-functional requirements for the Space Debris
   Tracking & Collision Risk Dashboard system. It establishes a formal agreement regarding
   system capabilities, performance expectations, constraints, and architectural design.
   1.2 Problem Statement
   The increasing population of orbital debris presents a measurable collision risk to
   operational spacecraft. Mission operators require software capable of identifying potential
   close approaches in a clear, interpretable, and timely manner. This system ingests debris
   catalogs, simulates short-term motion using a constant-velocity approximation, computes
   encounter metrics (minimum separation, time of closest approach, relative velocity), and
   presents ranked collision risk results through a mission-operations style dashboard.
9. Overall System Description
   The system accepts publicly available or synthetic debris catalogs containing position and
   velocity vectors. Using simplified linear propagation over configurable time windows, it
   computes:

- Minimum separation distance
- Time of Closest Approach (TCA)
- Relative velocity at encounter
- Transparent and interpretable composite risk score
  Results are presented through an interactive dashboard including a sortable alert table, a
  timeline of predicted close approaches, and visualizations of encounter geometry. The
  emphasis is on clarity, explainability, and rapid situational awareness rather than highfidelity orbital mechanics.

3. Statement of Functional Requirements
   Task 1: Upload or Generate Debris Catalog
   FR-1.1: The system shall accept CSV debris catalogs.
   FR-1.2: The system shall validate schema and data types.
   FR-1.3: The system shall generate synthetic debris objects.
   FR-1.4: The system shall display object count.
   Task 2: Define Spacecraft Parameters
   FR-2.1: The system shall allow input of position vectors (x,y,z).
   FR-2.2: The system shall allow input of velocity vectors (vx,vy,vz).
   FR-2.3: The system shall allow definition of safety radius.
   FR-2.4: The system shall validate numeric inputs.
   Task 3: Execute Collision Risk Analysis
   FR-3.1: The system shall simulate constant-velocity motion.
   FR-3.2: The system shall compute time of closest approach (TCA).
   FR-3.3: The system shall compute minimum separation distance.
   FR-3.4: The system shall compute relative velocity at encounter.
   FR-3.5: The system shall compute a transparent, interpretable severity risk score.
   FR-3.6: The system shall rank debris objects by severity.
   FR-3.7: The system shall provide an application interface for initiating and retrieving
   analysis results.
   Task 4: Visualize Results
   FR-4.1: The system shall display a sortable alert table.
   FR-4.2: The system shall display a timeline of close approaches.
   FR-4.3: The system shall display distance-versus-time plots.
   FR-4.4: The system shall display 2D encounter geometry visualizations.
   FR-4.5: The system shall allow export of analysis results as CSV.
4. Non-Functional Requirements
   Reliability
   The system shall produce consistent and repeatable results for identical inputs.
   Robustness
   The system shall handle invalid inputs gracefully and provide informative error messages.
   Performance
   The system shall analyze up to 1,000 debris objects within 5 seconds on a standard laptop.
   Maintainability
   The system shall follow a modular architecture separating ingestion, simulation, analysis,
   and visualization components.
   Usability
   The system shall prioritize clarity and explainability in the presentation of risk metrics to
   support rapid situational awareness.
5. System Models and Diagrams
   5.1 Use Case Diagram
   Primary Actor: Mission Operator
   Figure 1: Use Case Diagram – Mission Operator interacting with system functions.
   5.2 Sequence Diagram
   Sequence: User → UI → Backend API → Simulation Engine → Collision Engine → Results →
   UI
   Figure 2: Sequence Diagram – Analysis workflow from upload to result visualization.
   5.3 System Architecture Diagram
   Layered modular architecture separating presentation, application, simulation, analysis,
   and data layers.
   Figure 3: System Architecture Diagram – Layered separation of concerns.
6. Design and Implementation Constraints
   Standards Compliance
   The SRS structure follows guidance from Humphrey (2000), Introduction to the Team
   Software Process.
   Date/time representations shall follow ISO 8601 standards.
   Development Constraints
   The system shall be implemented in Python using open-source libraries.
   The motion model shall use a constant-velocity approximation.
   Development must be completed within the academic semester timeframe.
7. References and Sources of Information
   Humphrey, W. S. (2000). Introduction to the Team Software Process. Addison-Wesley.
   NASA Orbital Debris Program Office publications.
   ISO 8601 Standard for Date and Time Representation.
