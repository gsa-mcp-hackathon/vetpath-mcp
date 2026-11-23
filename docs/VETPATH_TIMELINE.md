# VetPath Transition Timeline v0.1

## Purpose

The VetPath timeline provides a controlled, machine-readable set of
military-to-civilian transition milestones.

The initial catalog is based on the VA Benefits and Services
*Know Before You Go Workbook*, version 1.

## Controlled phases

- `twelve_to_nine_months_before`
- `nine_to_three_months_before`
- `three_months_before_to_three_months_after`
- `three_to_twelve_months_after`
- `twelve_months_after_and_beyond`

These values preserve the organizing framework used by the source
workbook. They are planning windows, not independent eligibility rules.

## Source-page convention

`source_page` refers to the printed page number appearing in the
workbook footer rather than the PDF file's physical page index.

## Safety and scope

The catalog:

- contains no Veteran records, PII, PHI, or claims information;
- does not determine individual eligibility;
- does not replace official agency instructions;
- does not provide medical, legal, or financial advice;
- identifies the source document, version, page, and review status;
- links milestones to resource IDs when a reviewed catalog record exists.

The source PDF itself is not committed to the repository unless
redistribution is explicitly approved.

## MVP limitation

Version 0.1 contains a reviewed subset of high-value transition
milestones. It is not an exhaustive representation of every task,
benefit, deadline, exception, branch-specific requirement, or program.

## MCP retrieval tool

`get_transition_milestones` retrieves reviewed milestones for exactly
one controlled transition phase.

Inputs:

- `transition_phase` — required controlled phase
- `service_category` — optional controlled category
- `limit` — optional result limit from 1 through 50

The tool returns the shared VetPath response envelope. Each milestone
preserves source timing, next steps, important notes, related resource
IDs, workbook version, printed page number, and review status.

The tool does not infer a separation date, calculate legal deadlines,
determine eligibility, or replace current official agency guidance.
