# Domain event names
REPORT_SUBMITTED = "report.submitted"       # payload: {report_id, fund_type, pdf_url}
REPORT_DOWNLOADED = "report.downloaded"     # payload: {report_id, pdf_hash}
REPORT_EXTRACTED = "report.extracted"       # payload: {report_id, text, page_count}
REPORT_ANALYZED = "report.analyzed"         # payload: {report_id, fund_type, quality_score}
SCORE_CALCULATED = "report.scored"          # payload: {fund_id, final_score}
