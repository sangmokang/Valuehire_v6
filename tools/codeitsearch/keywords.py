"""Bilingual search keyword sets per segment.

사장님 규칙 — 국문·영문을 **모두** 빠짐없이 넣는다. 한 언어만 넣으면 사람인·잡코리아 이력서에서
한글로만 자기 직무를 쓰는 사람(국내 경력자 다수)과 영문 타이틀만 쓰는 사람(외국계·시니어)이
번갈아 누락된다.

Each segment carries four tiers:
  core      — the role itself; a candidate without one of these is usually off-target
  expanded  — how strong practitioners actually label their own work. These surface the
              people a title-only search never reaches, and are the reason the search
              keeps going instead of stopping at the first screenful.
  stack     — concrete tools/frameworks/certs that prove hands-on depth
  preferred — domain and seniority signals; they raise fit, never filter

``terms(segment)`` flattens every tier into the full de-duplicated query vocabulary.
"""

from __future__ import annotations

__all__ = ("SEGMENT_KEYWORDS", "TIERS", "terms", "tier")

TIERS = ("core", "expanded", "stack", "preferred")

SEGMENT_KEYWORDS: dict[str, dict[str, tuple[str, ...]]] = {
    "software_engineering": {
        "core": (
            "백엔드 개발자", "백엔드 엔지니어", "서버 개발자", "서버 엔지니어", "웹 백엔드",
            "Backend Engineer", "Backend Developer", "Server Developer", "Software Engineer",
        ),
        "expanded": (
            "마이크로서비스", "MSA", "대용량 트래픽", "분산 시스템", "아키텍처 설계",
            "성능 최적화", "쿼리 튜닝", "동시성 제어", "이벤트 기반", "메시지 큐",
            "테스트 코드", "리팩터링", "CI/CD", "인프라 운영", "모니터링", "장애 대응",
            "API 설계", "코드 리뷰", "기술 리드", "테크리드",
            "Microservices", "Distributed Systems", "High Traffic", "Scalability",
            "Event Driven", "Query Optimization", "Observability", "SRE",
            "Platform Engineering", "Domain Driven Design", "Clean Architecture",
            "Tech Lead", "System Design",
        ),
        "stack": (
            "Java", "Kotlin", "Spring", "Spring Boot", "JPA", "Node.js", "NestJS",
            "TypeScript", "Python", "Django", "FastAPI", "Go", "PostgreSQL", "MySQL",
            "Redis", "Kafka", "Elasticsearch", "Docker", "Kubernetes", "AWS", "Terraform",
            "GraphQL", "gRPC",
        ),
        "preferred": (
            "에듀테크", "이러닝", "SaaS", "B2B SaaS", "스타트업", "오픈소스", "기술 블로그",
            "EdTech", "Open Source",
        ),
    },
    "product_management": {
        "core": (
            "프로덕트 매니저", "프로덕트 오너", "서비스 기획자", "PM", "PO",
            "Product Manager", "Product Owner",
        ),
        "expanded": (
            "제품 전략", "로드맵", "요구사항 정의", "가설 검증", "A/B 테스트", "실험 설계",
            "데이터 기반 의사결정", "지표 설계", "리텐션", "전환율", "퍼널 분석",
            "유저 리서치", "사용자 인터뷰", "우선순위", "백로그", "스프린트", "그로스",
            "Product Discovery", "Roadmap", "OKR", "North Star Metric", "Experimentation",
            "Retention", "Activation", "Funnel Analysis", "Growth Product Manager",
            "User Research", "PRD", "Data Driven",
        ),
        "stack": (
            "SQL", "Amplitude", "Mixpanel", "GA4", "Google Analytics", "Figma", "Jira",
            "Notion", "Looker", "Tableau", "BigQuery",
        ),
        "preferred": (
            "에듀테크", "이러닝", "구독 서비스", "B2C", "LMS", "AI 프로덕트",
            "EdTech", "Subscription", "AI Product",
        ),
    },
    "product_design": {
        "core": (
            "프로덕트 디자이너", "UX 디자이너", "UI 디자이너", "UX/UI 디자이너", "서비스 디자이너",
            "Product Designer", "UX Designer", "UI Designer",
        ),
        "expanded": (
            "디자인 시스템", "컴포넌트 설계", "인터랙션 디자인", "프로토타이핑", "와이어프레임",
            "유저 플로우", "정보 구조", "사용성 테스트", "유저 리서치", "접근성",
            "디자인 토큰", "반응형 디자인", "디자인 QA", "핸드오프", "디자인 스프린트",
            "Design System", "Interaction Design", "Prototyping", "Usability Test",
            "Information Architecture", "Design Token", "Accessibility", "Design Ops",
            "Component Library", "Responsive Design", "User Flow",
        ),
        "stack": ("Figma", "Sketch", "Adobe XD", "Framer", "Protopie", "Zeplin", "Storybook"),
        "preferred": (
            "에듀테크", "이러닝", "B2C 앱", "포트폴리오", "디자인 리드",
            "EdTech", "Design Lead", "Portfolio",
        ),
    },
    "security": {
        "core": (
            "정보보안", "보안 담당자", "보안 엔지니어", "정보보호 담당자", "개인정보보호",
            "Security Engineer", "Information Security", "Security Manager",
        ),
        "expanded": (
            "ISMS-P", "ISMS 인증", "정보보호 관리체계", "취약점 진단", "모의해킹",
            "침해사고 대응", "보안 관제", "보안 정책 수립", "보안 감사", "개인정보 영향평가",
            "클라우드 보안", "접근통제", "계정 관리", "로그 분석", "내부통제",
            "개인정보보호법", "망분리", "보안 교육", "위험 평가",
            "Vulnerability Assessment", "Penetration Test", "Incident Response",
            "SIEM", "SOC", "Cloud Security", "DevSecOps", "Zero Trust", "IAM",
            "Security Audit", "Privacy Compliance", "GDPR", "ISO 27001", "Risk Assessment",
        ),
        "stack": ("AWS Security", "CSPM", "WAF", "EDR", "Splunk", "CISSP", "CISA", "정보보안기사"),
        "preferred": (
            "스타트업 보안", "SaaS", "CISO", "보안 총괄", "에듀테크", "EdTech",
        ),
    },
    "marketing": {
        "core": (
            "마케팅 매니저", "퍼포먼스 마케터", "그로스 마케터", "디지털 마케터", "브랜드 마케터",
            "Marketing Manager", "Performance Marketer", "Growth Marketer",
        ),
        "expanded": (
            "퍼포먼스 마케팅", "매체 운영", "광고 운영", "예산 집행", "ROAS 개선",
            "CAC", "LTV", "어트리뷰션", "전환 최적화", "랜딩페이지 최적화", "A/B 테스트",
            "CRM 마케팅", "라이프사이클 마케팅", "리텐션 마케팅", "콘텐츠 마케팅",
            "바이럴", "SEO", "그로스 해킹", "퍼널 설계", "리드 제너레이션",
            "Paid Media", "ROAS", "Attribution", "Funnel Optimization", "Growth Hacking",
            "Lifecycle Marketing", "Retention Marketing", "Content Marketing",
            "Demand Generation",
        ),
        "stack": (
            "Meta Ads", "Google Ads", "GA4", "Appsflyer", "Adjust", "Braze", "Amplitude",
            "네이버 GFA", "카카오모먼트", "Criteo", "Looker Studio",
        ),
        "preferred": (
            "에듀테크", "이러닝", "구독", "부트캠프", "커뮤니티", "B2C",
            "EdTech", "Bootcamp", "Subscription",
        ),
    },
    "sales": {
        "core": (
            "영업", "B2B 영업", "기업영업", "세일즈 매니저", "솔루션 영업", "교육영업",
            "Sales Manager", "B2B Sales", "Account Executive", "Enterprise Sales",
        ),
        "expanded": (
            "신규 고객 발굴", "제안서 작성", "입찰", "RFP 대응", "계약 협상", "키 어카운트",
            "파이프라인 관리", "목표 달성", "실적 관리", "고객사 관리", "리드 발굴",
            "인사이드 세일즈", "컨설팅 영업", "재계약", "업셀", "크로스셀",
            "기업교육 영업", "HRD 영업", "공공 영업",
            "Solution Sales", "Inside Sales", "SDR", "BDR", "Pipeline Management",
            "Quota Attainment", "Consultative Selling", "Key Account", "Renewal", "Upsell",
        ),
        "stack": ("Salesforce", "HubSpot", "CRM", "Notion", "Excel"),
        "preferred": (
            "에듀테크", "기업교육", "HRD", "L&D", "B2B SaaS", "공공기관", "EdTech",
        ),
    },
    "education_operations": {
        "core": (
            "교육 운영", "교육 기획", "교육 매니저", "과정 운영", "프로그램 매니저",
            "부트캠프 운영", "러닝 매니저",
            "Education Operations", "Program Manager", "Training Operations",
        ),
        "expanded": (
            "커리큘럼 운영", "기수 운영", "수강생 관리", "강사 관리", "만족도 조사",
            "운영 프로세스 개선", "매뉴얼 작성", "KPI 관리", "지표 관리", "리드 운영",
            "고용노동부 과정", "K-디지털 트레이닝", "국비 과정", "HRD-Net",
            "기업교육 운영", "온보딩", "학습 경험", "수료율 관리",
            "Bootcamp Operations", "Cohort Management", "Learning Experience",
            "Student Success", "Process Improvement", "Vendor Management", "L&D", "HRD",
        ),
        "stack": ("LMS", "Notion", "Excel", "Google Sheets", "Slack", "Zendesk"),
        "preferred": ("에듀테크", "이러닝", "부트캠프", "기업교육", "EdTech"),
    },
    "education_admin": {
        "core": (
            "교육 행정", "교육 지원", "학사 행정", "과정 행정", "교육 어드민",
            "Education Administrator", "Training Administrator",
        ),
        "expanded": (
            "수강 등록", "출결 관리", "증빙 서류", "정산", "국비 지원 과정", "HRD-Net",
            "고용노동부", "훈련과정 신고", "행정 처리", "문서 관리", "백오피스",
            "Course Administration", "Enrollment", "Compliance Documentation",
            "Grant Reporting", "Back Office",
        ),
        "stack": ("Excel", "Google Sheets", "LMS", "HRD-Net"),
        "preferred": ("에듀테크", "K-디지털 트레이닝", "국비교육", "EdTech"),
    },
    "customer_experience": {
        "core": (
            "CX 매니저", "고객경험", "고객성공", "CS 매니저", "커스터머 석세스",
            "Customer Experience Manager", "Customer Success Manager", "CX Manager",
        ),
        "expanded": (
            "VOC 분석", "NPS", "CSAT", "고객 응대", "상담 품질 관리", "응대 매뉴얼",
            "온보딩 설계", "이탈 방지", "리텐션", "문의 대응 프로세스", "FAQ 고도화",
            "채널 운영", "지표 관리", "CS 자동화", "챗봇 운영",
            "Churn Reduction", "Support Operations", "Playbook", "Ticket Management",
            "Onboarding", "Customer Journey",
        ),
        "stack": ("Zendesk", "채널톡", "Channel Talk", "Freshdesk", "Intercom", "Notion"),
        "preferred": ("에듀테크", "구독 서비스", "SaaS", "B2C", "EdTech"),
    },
    "content_video": {
        "core": (
            "영상 PD", "영상 제작", "영상 편집자", "콘텐츠 PD", "미디어 PD",
            "Video Producer", "Content Producer", "Video Editor",
        ),
        "expanded": (
            "기획부터 편집까지", "촬영", "조명", "스토리보드", "구성안 작성", "모션그래픽",
            "숏폼", "유튜브 채널 운영", "썸네일 기획", "후반 작업", "색보정", "자막",
            "브랜디드 콘텐츠", "스튜디오 운영", "온라인 강의 촬영",
            "Motion Graphics", "Short Form", "Post Production", "Storyboard",
            "Branded Content",
        ),
        "stack": (
            "Premiere Pro", "After Effects", "DaVinci Resolve", "Final Cut Pro",
            "Photoshop", "Illustrator",
        ),
        "preferred": ("에듀테크", "온라인 강의", "교육 콘텐츠", "EdTech"),
    },
    "hr_ga": {
        "core": (
            "총무", "총무 매니저", "경영지원", "HR 매니저", "인사총무", "오피스 매니저",
            "General Affairs", "HR Manager", "Office Manager",
        ),
        "expanded": (
            "자산 관리", "비품 관리", "시설 관리", "구매", "계약 관리", "업체 관리",
            "사무실 이전", "노무 대응", "급여 지원", "복리후생", "사내 행사", "안전관리",
            "Facility Management", "Asset Management", "Procurement",
            "Workplace Operations", "Labor Compliance", "Vendor Contract",
        ),
        "stack": ("Excel", "Google Sheets", "ERP", "Notion"),
        "preferred": ("스타트업", "스케일업", "IT 기업", "Scale-up"),
    },
    "instructor_mentor": {
        "core": ("강사", "멘토", "보조강사", "튜터", "Instructor", "Mentor", "Teaching Assistant"),
        "expanded": (
            "커리큘럼 기획", "강의 설계", "부트캠프", "커리어 코칭", "모의면접", "이력서 첨삭",
            "Curriculum Design", "Bootcamp", "Career Coaching", "Mock Interview",
        ),
        "stack": (),
        "preferred": ("에듀테크", "EdTech"),
    },
    "talent_pool": {"core": ("인재풀", "Talent Pool"), "expanded": (), "stack": (), "preferred": ()},
    "content_partner": {
        "core": ("콘텐츠 파트너", "Content Partner"),
        "expanded": (),
        "stack": (),
        "preferred": (),
    },
    "unsegmented": {"core": (), "expanded": (), "stack": (), "preferred": ()},
}


def tier(segment: str, name: str) -> list[str]:
    """One keyword tier for a segment, empty when the segment or tier is unknown."""
    if name not in TIERS:
        raise ValueError(f"unknown tier {name!r}; expected one of {TIERS}")
    entry = SEGMENT_KEYWORDS.get(segment)
    return list(entry.get(name, ())) if entry else []


def terms(segment: str) -> list[str]:
    """Every keyword for a segment, de-duplicated, in tier order."""
    seen: set[str] = set()
    ordered: list[str] = []
    for name in TIERS:
        for word in tier(segment, name):
            if word not in seen:
                seen.add(word)
                ordered.append(word)
    return ordered
