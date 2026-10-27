# How Introductions Are Built in LiDAR Degeneracy / LiDAR SLAM Robustness Papers

Compiled: 2026-10-11. Purpose: copy the *structure* of these introductions for our own Introduction, not their wording.
All descriptions below are paraphrases. Only short headings and labels are quoted.

## Sources and method

| # | Paper | Venue | Source read |
|---|---|---|---|
| 1 | X-ICP (Tuna et al.) | IEEE T-RO 40, 2024 | https://arxiv.org/html/2211.16335 (abs: https://arxiv.org/abs/2211.16335) |
| 2 | DCReg (Hu et al.) | IJRR 2026 (SAGE) | Project PDF `2509.06285v3.pdf`; https://arxiv.org/abs/2509.06285 |
| 3 | Informed, constrained, aligned (Tuna et al.) | IEEE T-FR 2025 | https://arxiv.org/html/2408.11809 |
| 4 | Switch-SLAM (Lee et al.) | IEEE RA-L 9(8), 2024 | Project PDF `SwitchSLAM.pdf` (DOI 10.1109/LRA.2024.3421792) |
| 5 | Probabilistic degeneracy detection (Hatleskog & Alexis) | IEEE RA-L 9(12), 2024 | https://arxiv.org/html/2410.10784 |
| 6 | FAST-LIO2 (Xu et al.) | IEEE T-RO 38(4), 2022 | https://arxiv.org/html/2107.06829 |
| 7 | Learning-based localizability (Nubert et al.) | IROS 2022 | https://arxiv.org/html/2203.05698 |

How accurate the numbers are:
- **DCReg and Switch-SLAM:** exact. The introduction text from the project PDFs was word-counted with `wc`, and citations were extracted with a regex.
- **The five arXiv papers:** approximate. This session's network proxy blocks arxiv.org for direct download (HTTP 403 policy), so these papers were read through WebFetch, a model-summarized view of the arXiv HTML. Their word counts are within roughly 10-15%. Their citation counts are the summarizer's tallies, cross-checked where two passes agreed.
- **Word counts** cover introduction body text, including any bullet lists, and exclude figure captions and footnotes.

---

## 1. X-ICP — Tuna et al., IEEE T-RO 2024

- **Length:** about 1,050 words in 8-9 paragraph blocks. The HTML splits the opening context in two around the teaser figure.
- **Citations:** 17 distinct, [1]-[17].
- **Internal signposting:** one unheaded opening, then run-in heads "a) Point Cloud Registration", "b) Current Limitations", "c) Proposed Approach" and "d) Contributions".

**Moves, in order:**
1. **Context:** robots need dependable localization and mapping. Infrastructure aids are costly, so the focus is on exteroceptive SLAM with LiDAR [1-3].
2. **Credibility of the field:** LiDAR pipelines do well on standard benchmarks (KITTI, HILTI) [4,5].
3. **a) Technical background:** scan-to-scan versus scan-to-map registration, with ICP as the workhorse [6-9].
4. **b) Problem definition and scope** (longest paragraph, about 290 words):
   - ICP has four error sources [10,11]. The paper chooses one of them: missing geometric constraints.
   - It names typical degenerate places (tunnels, open areas, corridors, doorways) [13] and points to Fig. 1.
   - It argues that registration must be localizability-aware [14-16].
5. **c) Proposed approach:**
   - Names X-ICP and points to Fig. 2 (system overview).
   - Describes the detection module and how it differs from the closest prior work.
6. **Approach, continued:** what the optimization module does with each localizability category.
7. **Evaluation preview:** simulation plus real-world tests, beating two named baselines [12,17]. Refers to Fig. 1 again.
8. **d) Contributions:** 4 bullets.
9. **Pointer:** one line sending the reader to the project page for supplementary material and video.

**Contribution list:**
- 4 bullets, all noun phrases: "A heuristic-free and multi-category ...", "A method to salvage ...", "A novel localizability-aware constrained ...", "A variety of experiments ...".
- The last item covers the experiments.

**Figures:**
- Fig. 1 is a teaser: a ground-truth map of an underground mine beside error-coloured maps from the proposed method and two state-of-the-art methods. It is referenced in b) and again in the evaluation preview.
- Fig. 2, the system overview, is referenced in c).

**Roadmap:** none.

**Gap, in our words:** in self-similar or featureless surroundings, the registration optimization is steered by noise along weakly constrained directions, so modern LiDAR SLAM still fails. Registration therefore needs a fine-grained, tuning-free sense of which directions are localizable.

**Limitations and hedges:** there is an explicit scope restriction (only the lack-of-constraints error source is addressed; a poor initial prior is acknowledged but set aside). The intro states no weaknesses of the method itself.

**Voice:** the word "we" never appears. The paper uses "this work", "the proposed framework" and passive voice, in the present tense.

**Related work:** separate Section II, with three subsections (registration methods, degeneracy detection, constrained optimization).

---

## 2. DCReg — Hu et al., IJRR 2026

- **Length:** 1,025 words (exact) in 8 paragraphs, including 3 bullets.
- **Citations:** 25 distinct (author-year).
- **Internal signposting:** two numbered subsections, "1.1 Motivation and Challenges" and "1.2 Contributions".

**Moves, in order:**
1. **Context and importance** (88 words): LiDAR perception underpins autonomy. Registration feeds motion estimation, mapping, localization, calibration and planning, backed by one long list of 13 citations.
2. **Problem, consequence, prior paradigm and three limitations** (347 words, the longest):
   - Degenerate scenes (corridors, tunnels, open fields) give a near-singular information matrix. The problem becomes ill-conditioned, noise is amplified, and navigation fails.
   - Current methods follow a "detect-then-mitigate" pattern and have made progress, but three linked challenges remain. These appear as bullets with bold run-in labels: Unreliable Detection, Insufficient Characterization and Limited Mitigation. Each bullet carries its own citations.
3. **Gap restated as a research question** (82 words, no citations): the paper asks whether a self-contained numerical framework can solve the problem, then lists three requirements (i)-(iii) that mirror the three challenges one to one.
4. **1.2 lead-in:** one sentence saying the paper introduces a framework.
5. **First contribution:** coupling-aware detection (Section 4). It is contrasted with full-Hessian methods, with citations and pointers to Section 3.3 and Sections 4.2-4.4.
6. **Second contribution:** physically interpretable characterization (Section 5). It opens with a motivating problem (eigenbasis ambiguity) before naming the contribution.
7. **Third contribution:** solution-preserving preconditioned mitigation (Section 6), contrasted with regularization methods.
8. **Fourth contribution:** experiments (Section 7.5), including a numeric speed-up claim (5-30x, up to 116x).

**Contribution list:**
- 4 contributions, each written as a full paragraph that opens with "Our first / second / third / fourth contribution (Section N) is ...".
- Each paragraph maps a contribution to a section and contrasts it with cited prior work.
- First person ("we", "our") is used throughout.

**Figures:** no teaser. The intro references no figure. Fig. 1 is a technical concept figure in Section 3.3.

**Roadmap:** none. The section pointers inside the contributions do that job.

**Gap, in our words:** today's detect-then-mitigate pipelines fail at all three stages:
- **Detection:** they mis-detect because the scale gap and coupling between rotation and translation hide the true spectrum.
- **Characterization:** they cannot say which physical motions are weak, or by how much.
- **Mitigation:** they alter the least-squares problem itself, which damages directions that were well constrained.

Section 2.4, "Research Gap", restates this with a comparison table (Table 1).

**Limitations and hedges:** none in the intro. The scope is framed as needing no external sensors. Limitations are postponed to Section 8, "Discussions and Limitations".

**Voice:** "we", "us" and "our"; present tense; one rhetorical question.

**Related work:** separate Section 2, with subsections on detection, characterization and mitigation, plus a Research Gap subsection.

---

## 3. Informed, constrained, aligned — Tuna et al., IEEE T-FR 2025 (arXiv version)

- **Length:** about 1,000-1,200 words in 8 paragraph blocks. Two summarizer passes gave 900-1,000 and about 1,200.
- **Citations:** about 36 distinct (author-year in the arXiv version).
- **Internal signposting:** run-in labels "Algorithmic limitations", "Defining LiDAR degeneracy", "Degenerate point cloud registration", "LiDAR degeneracy mitigation in the field" and "Contributions".

**Moves, in order:**
1. **Context:** LiDAR and SLAM in field robotics (about 7 citations).
2. **Background:** ICP sits at the core of LiDAR-SLAM frameworks (3 citations).
3. **Algorithmic limitations:** the ways ICP fails (2 citations).
4. **Defining LiDAR degeneracy:** a definition paragraph (4 citations).
5. **Degenerate point cloud registration:**
   - Surveys detection work (about 14 citations, the densest paragraph).
   - Notes that mitigation work is far thinner. This is the first statement of the gap.
   - Fig. 1 is placed here.
6. **Mitigation in the field:**
   - Existing mitigation work, and why the question is still open (about 11 citations).
   - Defines two classes of methods (active and passive) as a 2-item list.
   - Sets the scope to methods inside the ICP formulation.
7. **Pointer:** one line saying the related work for each class is in Section 2.2.2.
8. **Contributions:** lead-in, with a reference to Fig. 1, then 4 bullets.

**Contribution list:**
- 4 bullets, all noun phrases: "A thorough study ...", "The introduction, investigation, and discussion ...", "Comparison of the discussed methods ...", "The consolidation of open-source methods ...".
- The contributions fit an analysis or benchmark paper: a study, a comparison and an open-source release.

**Figures:** Fig. 1 is a teaser showing a legged-robot forest/open-field experiment, with each method's error-coloured map against ground truth. It is referenced in the contributions paragraph.

**Roadmap:** none.

**Gap, in our words:** detecting degeneracy has been studied a lot. How to mitigate it inside ICP once it is detected has not been compared systematically, especially in field conditions, and the question is still open.

**Limitations and hedges:**
- Scope statements: methods inside ICP only, field-robotics focus.
- Hedging about prior work, e.g. that some strategies are viable only for short periods.
- No limitations of the work itself.

**Voice:** no "we" or "our". The paper uses "this work" and "the authors", in the present tense.

**Related work:** separate Section 2, with subsections on robust registration and on degeneracy detection and mitigation (2.2.1-2.2.3).

---

## 4. Switch-SLAM — Lee et al., IEEE RA-L 2024

- **Length:** 395 words (exact) in 3 paragraphs plus a 3-item bullet list. By paragraph: 109, 81 and 63 words; the bullets are 45, 49 and 48 words.
- **Citations:** 15 distinct, [1]-[15]. All of them are in paragraphs 1-2. The approach and contribution text cites nothing.
- **Internal signposting:** no headings.

**Moves, in order:**
1. **Context, then sensor-specific failure modes:**
   - SLAM has progressed.
   - LiDAR SLAM degenerates in scenes without structure [1-3].
   - Visual SLAM fails under aggressive motion, changing light and missing texture [4-6].
2. **Existing approaches, then their limitation:**
   - LiDAR-visual fusion systems exist [7-13].
   - They rely on MAP fusion (iterated Kalman filter [14], factor graph [15]).
   - So when one sensor stays degenerate for a long time, its bad information spreads through the whole system.
3. **Approach and contributions lead-in:**
   - "we propose" Switch-SLAM, defined in one sentence and linked to Fig. 1.
   - One sentence on why the switching design solves the stated limitation.
   - Ends with a lead-in to the contribution list ("main contributions of our work").
4. **Contribution bullets:** 3 bullets, each with a bold run-in label ("Switching structure:", "Non-heuristic degeneracy detection:", "Experiments on various scenarios:") followed by 2-3 descriptive sentences.

**Figures:** Fig. 1 is a teaser with snapshots and maps from a simulated farm sequence (aggressive motion plus little structure). It is referenced in paragraph 3.

**Roadmap:** none.

**Gap, in our words:** LiDAR-visual systems built on MAP fusion cannot isolate a sensor that is degenerate for a long time, so one sensor's failure corrupts the joint estimate.

**Limitations and hedges:** none in the intro. The future work in the conclusion is the only self-limitation.

**Voice:** "we" and "our work" (the abstract uses "This letter"); present tense.

**Related work:** separate Section II, with subsections A (LiDAR odometry degeneration) and B (LiDAR-visual SLAM). Section II ends by restating the gap and the fix.

---

## 5. Hatleskog & Alexis — Probabilistic degeneracy detection, IEEE RA-L 2024

- **Length:** about 740 words in about 12 paragraph blocks.
- **Citations:** 20 distinct, [1]-[20].
- **Internal signposting:** Section I contains headed subsections "A. Related Work" and "B. Proposed Contribution". Section II is "Preliminaries & Problem Statement".

**Moves, in order:**
1. **Context and problem:** LiDAR registration fails where geometry is uninformative, and the estimated covariance can be over-confident [1-7].
2. **I-A, learning-based detection:** works once trained, but needs labels and compute [8,9].
3. **I-A, covariance estimation:** the literature and its gap [10-13].
4. **I-A, the seminal eigenvalue method:** [4,5,14].
5. **I-A, why threshold methods fail** (about 150 words): their thresholds depend on scale, weighting, the number of measurements and noise, so they do not generalize [14-20].
6. **I-B, approach overview:** a noise-grounded probabilistic test ("we").
7. **I-B, advantages:** benefits over the prior methods [14-17].
8. **I-B, positioning:** how the method plugs into point-to-plane minimization [1,4,14].
9. **I-B, validation overview:** previews the evaluation and refers to Fig. 1 [14,15,19].
10. **Contributions:** lead-in sentence plus 3 numbered items.
11. **Scope note:** one sentence on how normal covariances are obtained.
12. **Roadmap:** one sentence covering Sections II-V.

**Contribution list:** 3 numbered items, all noun phrases: "A new probabilistic and generalizable ...", "A probabilistic degeneracy-aware point-to-plane ...", "Experiments validating the approach ...". The last item covers the experiments.

**Figures:** Fig. 1 is a teaser comparing the proposed method with the main baseline [14] in an underground mine (legged robot) and in a cylindrical tank (flying robot). It is referenced in the validation paragraph.

**Roadmap:** yes, a single sentence.

**Gap, in our words:** detectors based on eigenvalues or condition numbers have to be retuned for every robot, sensor and environment. Learning-based detectors need labelled data. What is missing is a detector derived from the sensor's noise model that works without retuning.

**Limitations and hedges:**
- Hedged criticism of prior work.
- A scope note on the covariance inputs.
- No limitations of the method itself.

**Voice:** impersonal through the context and related work; "we" starts in I-B. Present tense.

**Related work:** inside the introduction (I-A). This is the RA-L space-saving option.

---

## 6. FAST-LIO2 — Xu et al., IEEE T-RO 2022 (system paper; robustness framing)

- **Length:** about 1,050-1,150 words in 5 paragraphs.
- **Citations:** 22 distinct, [1]-[22].
- **Internal signposting:** no headings.

**Moves, in order:**
1. **Context:** real-time SLAM and dense mapping matter, and vision-based approaches have limits [1-8].
2. **Why LiDAR:** its strengths, its applications, and new solid-state LiDARs [9-20].
3. **Problem definition** (about 460 words, the longest): four challenges, numbered inline [14-16].
4. **Gap, approach and contributions** (about 340 words):
   - "we address" the challenges with two key techniques.
   - Then four inline-numbered contributions, written verb-first ("We develop ...", "We integrate ...", "We conduct ...").
   - Mentions the open-source release [21,22].
5. **Roadmap:** a full paragraph giving the remaining sections.

**Contribution list:** 4 inline-numbered items inside a paragraph. They are the only verb-first, first-person contribution list in this sample.

**Figures:** Fig. 1 is the system pipeline. The intro does not reference it; it is first cited in Section III.

**Roadmap:** yes.

**Gap, in our words:** hand-tuned feature extraction breaks in structure-less scenes and across LiDAR types, and keeping a large, dense map searchable and updatable in real time costs too much computation.

**Limitations and hedges:** none about the method itself.

**Voice:** impersonal in paragraphs 1-3; "we" starts in paragraph 4. Present tense.

**Related work:** separate Section II, "Related Works".

---

## 7. Nubert et al. — Learning-based localizability estimation, IROS 2022 (conference)

- **Length:** about 550-600 words in 3 paragraphs.
- **Citations:** 6 distinct, [1]-[6].
- **Internal signposting:** no headings.

**Moves, in order:**
1. **Context and existing approaches:** LiDAR localization via scan-to-scan and scan-to-map registration [1-4]. The teaser figure follows this paragraph.
2. **Limitation, problem and gap** (about 220 words): registration breaks in degenerate scenes. Existing detectors need preprocessing, use thresholds tuned per environment, and need both scans, so none of them can judge a single scan [5,6].
3. **Approach, inline contributions and release** (about 230 words, no citations):
   - A learning-based, single-scan estimator trained in simulation.
   - Contributions i)-iii), introduced by a "main contributions of this work" lead-in. All are noun phrases: "The development of ...", "A thorough evaluation ...", "A thorough design and implementation ...".
   - Promises an open-source release.

**Figures:** Fig. 1 is a teaser from a field test in an underground mine, showing localizable and non-localizable segments and maps with and without detection. The text never references it.

**Roadmap:** none.

**Gap, in our words:** no existing method can tell, from a single scan and before registration, whether that scan will localize. Current detectors need costly preprocessing, environment-specific thresholds and a pair of scans.

**Limitations and hedges:** only modal hedging. No limitations of the method itself.

**Voice:** no "we" or "our"; "this work"; present tense, with future tense for the code release.

**Related work:** separate Section II, with no subsections.

---

## Cross-paper summary table

| Paper | Venue | Paragraphs | Words | Distinct cites | Cites / 100 words | Contribution list | Fig. 1 teaser (referenced?) | Roadmap | Related work | "we" |
|---|---|---|---|---|---|---|---|---|---|---|
| X-ICP | T-RO | 8-9 | ~1,050 | 17 | ~1.6 | 4 bullets, noun phrases | Yes (yes), plus Fig. 2 overview | No | Sec. II | No |
| DCReg | IJRR | 8 (two subsections) | 1,025 | 25 | ~2.4 | 4 paragraphs, "Our first contribution (Sec. N) is ..." | No (technical figure in Sec. 3) | No (section pointers instead) | Sec. 2, plus a Research Gap subsection and table | Yes |
| ICA | T-FR | 8 | ~1,000-1,200 | ~36 | ~3.3 | 4 bullets, noun phrases | Yes (yes) | No | Sec. 2 | No |
| Switch-SLAM | RA-L | 3 + bullets | 395 | 15 | ~3.8 | 3 bullets with bold labels | Yes (yes) | No | Sec. II | Yes |
| Hatleskog | RA-L | ~12 blocks (I, I-A, I-B) | ~740 | 20 | ~2.7 | 3 numbered, noun phrases | Yes (yes) | Yes | Inside intro (I-A) | Yes (from I-B) |
| FAST-LIO2 | T-RO | 5 | ~1,100 | 22 | ~2.0 | 4 inline-numbered, "We ..." | No (pipeline, not referenced) | Yes | Sec. II | Yes (from P4) |
| Nubert | IROS | 3 | ~570 | 6 | ~1.1 | 3 inline i)-iii), noun phrases | Yes (not referenced) | No | Sec. II | No |

---

## Synthesis: the common template for a T-RO / IJRR / RA-L introduction in this sub-field

### Length
- **Journals (T-RO, IJRR, T-FR):** about 1,000-1,200 words in 5-9 paragraphs, roughly one full two-column page. All four journal papers fall in this band.
- **RA-L letters:** about 400-750 words in 3-6 paragraphs plus the list.
  - The low end (Switch-SLAM, about 400) keeps related work in Section II.
  - The high end (Hatleskog, about 740) moves related work into the intro.
- **Conference (IROS):** about 550-600 words in 3 paragraphs.
- **Page budget behind these numbers (RAS pages):**
  - RA-L: 6 pages, plus at most 2 paid extra pages (8 total), with figures and references counted.
  - T-RO regular papers: at most 18 pages at first submission and 20 in the final version, with page charges above 12.

### Paragraph sequence

Present in nearly all seven papers:
1. **Context and importance:** LiDAR SLAM or registration is foundational for autonomy or field robotics. Citations come in long clustered lists.
2. **Technical background** (journals; optional in RA-L): scan-to-map registration, ICP, and the least-squares or Hessian view.
3. **Problem definition:**
   - What degeneracy is: weak or missing constraints, giving an ill-conditioned or near-singular Hessian.
   - Where it happens, always with concrete examples: corridors, tunnels, open fields, mines.
   - Why it matters: drift, divergence, failure.
   - Often anchored to a teaser Fig. 1.
4. **Existing approaches, grouped by family:** eigenvalue thresholds, condition numbers, probabilistic or covariance methods, learning-based methods, multi-sensor fusion. Citations are clustered per family.
5. **Limitation, then gap:**
   - A "however / yet / still" turn that pins a specific failing on a named family of methods.
   - Journals often enumerate 2-4 challenges (DCReg uses bullets; FAST-LIO2 numbers them inline).
   - DCReg also restates the gap as a research question, with requirements that map one-to-one onto the challenges.
6. **This paper's approach:**
   - Name and acronym, a one- or two-sentence key idea, and how it differs from the closest prior work.
   - Points to Fig. 1 or to a Fig. 2 system overview.
   - First person (where used) starts here.
7. **Evaluation preview** (journals and Hatleskog): settings (simulation and real), baselines, a headline result.
8. **Contribution list.**
9. **Optional closers:** a project-page or code link (X-ICP, FAST-LIO2, Nubert); a roadmap (only 2 of 7).

### Contribution-list conventions
- **Number of items:** 3-4 in every paper. RA-L, IROS and the one analysis paper use 3 or 4; T-RO and IJRR use 4.
- **The last item** is almost always the experimental validation and/or the open-source release (6 of 7).
- **Format:** bulleted list (3 of 7), numbered list (1), inline numbered items (2), or one paragraph per contribution with section pointers (DCReg, IJRR style).
- **Phrasing:**
  - Noun phrases dominate (4 of 7), e.g. "A heuristic-free ... method", "A probabilistic ... formulation", "Experiments validating ...".
  - Switch-SLAM uses a bold label followed by 2-3 explanatory sentences.
  - FAST-LIO2 is the only one that is verb-first ("We develop ...").
  - DCReg uses "Our N-th contribution (Section N) is ...".
- **Content of each item:** what the contribution is, plus the property that answers the gap (heuristic-free, generalizable, coupling-aware, solution-preserving).
- **Lead-in:** a one-line "main contributions are as follows".

### Fig. 1 usage
- **5 of 7 put a first-page teaser** that shows a real or simulated degenerate environment with qualitative map or trajectory results. It usually compares the proposed method with baselines through error-coloured point clouds or a ground-truth overlay.
- **4 of those 5 reference it in the text,** in the problem or approach paragraph, or in the contributions lead-in.
- **The papers without a teaser** (FAST-LIO2, a system paper; DCReg in IJRR) use Fig. 1 for the pipeline or a concept diagram, cited only from the method sections.
- **The system-overview figure** is usually Fig. 2 and is cited from the approach paragraph (X-ICP).

### Citation density
- **Journals:** 17-36 distinct citations in the intro, about 1.5-3.5 per 100 words.
- **RA-L:** 15-20 citations, about 2.5-4 per 100 words. Density is higher because the text is short and related work is folded in.
- **IROS:** 6 citations.
- **Placement:** citations sit in the first half (context, existing approaches, limitation). The approach and contribution paragraphs cite nothing, or only the baselines they are contrasted with (Switch-SLAM, Nubert and DCReg's research-question paragraph have zero).
- **IEEE style:** grouped ranges such as "[7]-[13]" are normal.

### Tense and voice
- **Present simple** is used for the state of the field, the problem, and what the method does ("X classifies ...", "the framework keeps ...").
- **Present perfect** is used for the field's progress (progress "has been made", methods "have been proposed").
- **Past tense** is used only when narrating a specific prior paper (mostly in Section II).
- **Future tense** is used only for promised code releases.
- **First person is split:**
  - 4 of 7 use "we" or "our" (DCReg, Switch-SLAM, Hatleskog, FAST-LIO2), but only from the approach paragraph onward. Context and related-work paragraphs stay impersonal.
  - 3 of 7 (all from ETH RSL: X-ICP, ICA, Nubert) avoid "we" entirely and use "this work" or "the proposed ...".
- **RA-L papers** call themselves a "letter" (Switch-SLAM).

### How the gap is stated
The typical form is one concrete deficiency of a named class of methods, followed by its consequence. Examples:
- Thresholds that do not transfer across robots, sensors or environments (Hatleskog, Nubert, X-ICP implicitly).
- Coupling and scale disparity that hide degeneracy (DCReg).
- MAP fusion that spreads a degenerate sensor's errors (Switch-SLAM).
- No systematic comparison of mitigation methods (ICA).
- No single-scan assessment (Nubert).

### Limitations and hedges
- No introduction lists weaknesses of its own method.
- Several state scope (X-ICP: one of four error sources; ICA: ICP-internal methods and field robotics; Hatleskog: a covariance-input note).
- Limitations are deferred to a Discussion/Limitations section (DCReg Sec. 8) or the conclusion.

### Related-work placement
- 6 of 7 use a separate Section II, and the intro still summarizes the method families in 1-2 paragraphs.
- Folding related work into the intro as I-A (Hatleskog) is a space-saving RA-L option.
- DCReg ends Section 2 with an explicit "Research Gap" subsection and a feature-comparison table, a pattern worth borrowing if we have space.

### Internal signposting
Longer introductions break up their text:
- run-in paragraph heads (X-ICP a)-d); ICA labels);
- numbered subsections (DCReg 1.1/1.2; Hatleskog I-A/I-B).

Short RA-L intros (Switch-SLAM) use none.

---

## IEEE guidance found (quoted only where a phrase is short; nothing invented)

**IEEE Author Center (Journals), "Structure Your Article"**
- URL: https://journals.ieeeauthorcenter.ieee.org/create-your-ieee-journal-article/create-the-text-of-your-article/structure-your-article/
- The Introduction should review the existing literature to place the work in its field and to "show the novelty of your work". It should describe the question the research answers and why that question matters.
- The page gives no guidance on intro length, tense, voice, contribution lists or figures. Its only length rule is for the abstract (up to 250 words).

**IEEE Author Center (Conferences), "Structure Your Paper"**
- URL: https://conferences.ieeeauthorcenter.ieee.org/write-your-paper/structure-your-paper/
- The Introduction should help the reader see why the research is important and what it contributes.
- Recommended flow: open with a brief overview of the current state of research, narrow to the specific topic, and end with the exact question or hypothesis the paper addresses. Authors should state their motivation and what the work adds.
- No guidance on tense, voice, figures or length.

**IEEE RAS, RA-L Information for Authors**
- URL: https://www.ieee-ras.org/publications/ra-l/information-for-authors-ra-l
- Page limit: 6 pages in two-column format, plus up to 2 extra pages with charges (maximum 8). Figures, tables, appendices and references all count.
- The only intro-specific note is formatting: give the first word of the Introduction a drop-cap initial.
- No writing guidance.

**IEEE RAS, T-RO Information for Authors**
- URL: https://www.ieee-ras.org/publications/t-ro/t-ro-information-for-authors/
- Page limits: regular papers at most 18 pages at first submission and at most 20 in the final version, with page charges beyond 12.
- Authors must "clearly specify in which way it goes beyond the state of the art."
- T-RO uses double-anonymous review (adopted January 2025). When citing your own earlier work, write in the third person ("a recent work [...] proposed ...") rather than "in our previous work". This directly affects how an intro positions the authors' own prior papers. Project-page or code links that reveal identity should also be checked against this policy.
- New authors are encouraged to read recent T-RO issues to learn the house style.

No IEEE page found here prescribes intro length, tense or voice, a Fig. 1 teaser, or a roadmap. Those conventions come from the papers above.

---

## Implications for our Introduction (structure only)

**For an RA-L-length paper,** aim for about 550-750 words. Two shapes work:
- 5-6 paragraphs plus 3 contributions, with related work in Section II;
- or the Hatleskog shape, with related work inside the intro as I-A/I-B.

**For a T-RO / IJRR-length paper,** aim for about 1,000-1,200 words, 4 contributions, and optional run-in heads.

**Suggested sequence:**
1. Context: LiDAR SLAM / registration matters.
2. Degeneracy: definition, concrete environments, and the failure it causes (point to Fig. 1).
3. Existing detection and mitigation families, with clustered citations.
4. Two or three specific shortcomings, then the gap.
5. "In this letter / paper, we propose ...": key idea and difference from the closest work.
6. Evaluation preview (journal only).
7. 3-4 contributions, ending with experiments and/or release.
8. Optional one-sentence roadmap.

**Other conventions to follow:**
- Keep the approach and contribution paragraphs nearly citation-free.
- Use present tense, and start "we" only from the approach paragraph.
- State scope, not weaknesses.
