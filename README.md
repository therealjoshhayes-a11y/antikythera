# Antikythera

Tools for the ethical application of machine learning 
in higher education credentialing.

---

## What this is

Antikythera is a collection of tools that apply machine learning 
to credentialing problems in higher education, without replacing 
human judgment in decisions that require it.

Each project in this repository addresses a specific alignment 
problem. All projects use the MinK review protocol.

---

## MinK

MinK (Minimum K) is the SME review protocol used across all 
Antikythera projects.

The operator sets K (queue depth per similarity measure) and 
acceptance_target (accepted pairs before the session ends). A 
three-person panel votes Accept or Not Accept on ranked pairs. 
When acceptance_target is reached, the session terminates.

The algorithm ranks. The panel decides.

---

## Projects

### Abulafia
Standards alignment for legacy degree programs.

Maps Student Learning Outcomes from existing Texas community college 
degree programs to external industry certifications and professional 
licensure frameworks. Produces a defensible, auditable crosswalk for 
accreditors and curriculum committees.

Frameworks aligned to date: USCG · NCCER · BCSP · NAPTA · SACA · DOT

See /abulafia for code and /abulafia/05_documentation for the 
technical manual and research supplement.

---

## What these tools do not do

Antikythera tools do not make credentialing decisions. They rank 
candidates and record what a qualified human panel decided.

---

## License

Proprietary. Contact [you] for institutional licensing.
