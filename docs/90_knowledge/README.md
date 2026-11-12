---
id: MOVE-90-KNOWLEDGE
type: migration-note
req_ids: []
status: done
sensitivity: internal
owner: AI-SE
version: 1.0.0
---

# docs/90_knowledge — 移設済み（2026-11-06）

本ディレクトリの文書は **`tools/kb-platform/repo/` へ移設**した。
知識庫を 2 つに分けないための措置である（ユーザー指示 2026-11-06）。

| 旧パス | 新パス（知識庫） | doc_id |
|---|---|---|
| `docs/90_knowledge/reference-design-book.md` | `tools/kb-platform/repo/company/templates/reference-design-book.md` | `TPL-DESIGN-REF-001` |
| `docs/90_knowledge/answer-engine.md` | `tools/kb-platform/repo/company/standards/requirements/answer-engine.md` | `STD-REQ-ANSWER-001` |
| `docs/90_knowledge/ai-dev-playbook.md` | `tools/kb-platform/repo/company/patterns/dev/ai-playbook.md` | `PAT-DEV-PLAYBOOK-001` |
| `docs/90_knowledge/platform-map.md` | `tools/kb-platform/repo/company/standards/platform-map.md` | `STD-PLATFORM-001` |
| `docs/90_knowledge/dual-deliverable.md` | `tools/kb-platform/repo/company/patterns/delivery/dual-deliverable.md` | `PAT-DELIVERY-002` |
| `docs/90_knowledge/onboarding-checklist.md` | `tools/kb-platform/repo/company/patterns/howto/onboarding.md` | `PAT-ONBOARDING-001` |
| `docs/90_knowledge/requirement-review-capability.md` | `tools/kb-platform/repo/company/patterns/review/review-capability.md` | `PAT-REVIEW-CAP-001` |
| `docs/90_knowledge/v1-platform-4layer.md` | `tools/kb-platform/repo/company/standards/v1-platform-4layer.md` | `STD-PLATFORM-4L-001` |
| `docs/90_knowledge/claude-code-migration-guide.md` | `tools/kb-platform/repo/company/patterns/howto/cc-migration.md` | `PAT-CC-MIGRATION-001` |
| `docs/90_knowledge/ppt-deviation-register.md` | `tools/kb-platform/repo/company/standards/ppt-deviation.md` | `STD-PPT-DEVIATION-001` |
| `docs/90_knowledge/ppt-coverage-assessment.md` | `tools/kb-platform/repo/company/standards/ppt-coverage.md` | `STD-PPT-COVERAGE-001` |
| `docs/90_knowledge/ppt-example-walkthrough.md` | `tools/kb-platform/repo/company/patterns/dev/ppt-walkthrough.md` | `PAT-DEV-WALKTHROUGH-001` |
| `docs/90_knowledge/internal/harmony-5gates.md` | `tools/kb-platform/repo/company/standards/internal/harmony-5gates.md` | `STD-INT-HARMONY-001` |
| `docs/90_knowledge/internal/sds2-lessons.md` | `tools/kb-platform/repo/company/standards/internal/sds2-lessons.md` | `STD-INT-SDS2-001` |
| `docs/90_knowledge/review_diff_assets/SOP-review-diff.md` | `tools/kb-platform/repo/company/patterns/review/sop-review-diff.md` | `PAT-REVIEW-SOP-001` |
| `docs/90_knowledge/review_diff_assets/_skeleton/review_comments.md` | `tools/kb-platform/repo/company/standards/review-log-skeleton.md` | `INC-SKELETON-REVIEW-001` |
| `docs/90_knowledge/agent-run-record.md` | `tools/kb-platform/repo/projects/P-R60-001/knowledge/agent-run-record.md` | `r60-001-10-agent-run-record` |

- 引用は新しいパスへ貼り替え済み。旧パスを新規に書かないこと。
- 正本は移設先。ここには文書を戻さない。
