# Bengali FAQ source audit — 11 Oct 2026

File: `backend/data/faqs/bengali_faqs.json` (30 entries).
Result: **12 verified, 18 PENDING.** `verified_on` = date the cited page was checked against the answer. `PENDING` = not yet confirmed. Either the page could not be opened by the audit tool, or it does not support the answer.

Context that affects many entries: West Bengal changed government in May 2026. Since then:
- Birth/death registrars were moved from panchayat pradhans and municipal heads to government officers (July 2026).
- Swasthya Sathi beneficiaries are to be merged into Ayushman Bharat.
- Several schemes are reported (secondary sources) as renamed or replaced: Lakshmir Bhandar → Annapurna, Duare Sarkar → Jan Kalyan Shivir.

Answers written before May 2026 should not be trusted for scheme names, amounts or eligibility.

| ID | Status | Source used | Issue found | Action |
|---|---|---|---|---|
| cert_01 | Verified | Janma-Mrityu Tathya pre-requisite PDF | Matches: address proof (Aadhaar/EPIC/Khadya Sathi) + discharge certificate | Date updated |
| cert_02 | Verified | Same PDF (hospital DEO sections; citizen online registration) | Old answer sent private/home births to gram panchayat. Pradhans stopped being registrars in July 2026. Old source PDF (2022) could not be opened | Answer rewritten without naming a registrar; source replaced |
| cert_03 | Verified | CRS FAQ (dc.crsorgi.gov.in, Registrar General of India) | 21-day normal period and delayed registration under Sec. 13 confirmed. Old source was the portal homepage, which doesn't mention 21 days | Source replaced |
| cert_04 | Verified | janma-mrityutathya.wb.gov.in (Citizen Services menu) | Death: apply / track / download all listed | Date updated |
| cert_05 | Verified | castcertificatewb.gov.in/how_to_apply | Steps match. Department confirmed via cm.wb.gov.in scheme list (Backward Classes Welfare) | Date updated |
| cert_06 | PENDING | castcertificatewb.gov.in/searchappl | Page blocked to the audit tool | Check in browser |
| cert_07 | Verified | s24pgs.gov.in Bhangore-I block citizen services | Old source was the wb.gov.in homepage. Official page: apply on e-District, SDO approves; birth, citizenship, age proof + photo | Answer rewritten; source replaced. One block's page, so ask locally if documents differ |
| cert_08 | Verified | s24pgs.gov.in (docs, e-District, BDO); murshidabad.gov.in (BDO rural / SDO urban) | Old answer said "municipality" for urban. Official: SDO office | Answer rewritten; source replaced |
| cert_09 | Verified | Janma-Mrityu Tathya pre-requisite PDF + portal menu | Correction service exists; online form needs one address proof | Vague "relevant documents" replaced with the listed proof |
| cert_10 | Verified | Portal menu ("Download Certificate", "Know your acknowledgement/Certificate No") | Older paper certificates may not be downloadable | Added "if not on portal, contact the registering office" |
| scheme_01 | PENDING | ds.wb.gov.in (blocked) | Duare Sarkar reportedly replaced by Jan Kalyan Shivir (jks.wb.gov.in, blocked; secondary source only). Old answer listed schemes since changed | Outdated scheme list removed; check jks.wb.gov.in |
| scheme_02 | PENDING | wcdsw.wb.gov.in (blocked) | Secondary sources: replaced by Annapurna Bhandar from 1 Jun 2026 (₹3,000/month, ages 25–60). Not confirmed on an official page | Answer made conservative (no amounts/eligibility). Check socialregistry.wb.gov.in |
| scheme_03 | Verified | newsonair.gov.in (23 May 2026) | Swasthya Sathi beneficiaries to be merged into Ayushman Bharat from July 2026 | Answer rewritten; keyword "আয়ুষ্মান" added. Implementation status after July not confirmed |
| scheme_04 | Verified | krishakbandhu.wb.gov.in/about_kb | Registration at block ADA office confirmed. Page may predate the May 2026 change | Date updated |
| scheme_05 | PENDING | kanyashree.wb.gov.in (blocked) | Scheme status under new government not confirmed | Check in browser |
| scheme_06 | PENDING | wb.gov.in/government-schemes.aspx | Page lists no welfare schemes, so it does not support the answer | Find the Jai Bangla / old-age pension page |
| scheme_07 | PENDING | food.wb.gov.in (blocked) | — | Check in browser |
| scheme_08 | PENDING | pmayg.nic.in (blocked) | — | Check in browser |
| scheme_09 | PENDING | nrega.dord.gov.in (nrega.nic.in now redirects here) | Landing page has no job-card text | Source URL updated; find the job-card page |
| scheme_10 | PENDING | wb.gov.in schemes page | Source does not support the answer. Answer is generic advice | Find a source or drop entry |
| pan_01–05, 07, 10 | PENDING | prd.wb.gov.in homepage | Homepage shows news items only, no procedures | Find specific P&RD pages or district pages |
| pan_06 | PENDING | wb.gov.in homepage | Homepage alone is not evidence | Find trade-licence page |
| pan_08 | PENDING | wb.gov.in homepage | Answer correctly avoids inventing a number. CMO grievance portal (cmo.wb.gov.in) exists but was blocked to the tool | Check cmo.wb.gov.in before adding it |
| pan_09 | Verified | psc.wb.gov.in/rti.jsp | PSC's own RTI disclosure; quotes WB RTI Rules 2006 (₹10 court fee) | Fee sentence added |

"Blocked" means the site refused automated access (robots.txt). It does not mean the page is broken. These must be opened in a normal browser.
