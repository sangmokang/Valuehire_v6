# ABB 로보틱스 제품군·소프트웨어 생태계·경쟁 환경 조사 보고서 (기준일 2026-10-28)

## 0. 요약 (핵심 10줄)

1. ABB는 2025-10-08 로보틱스 사업부를 SoftBank Group에 기업가치 53.75억 달러로 매각하기로 합의했고, 2026년 중·후반 클로징 예정이다. 2025년 4분기부터 로보틱스는 "중단영업(Discontinued operations)"으로 분류됐다. (출처: https://group.softbank/en/news/press/20251008 , https://www.abb.com/global/en/news/129776/abb-to-divest-robotics-division-to-softbank-group)
2. 매각 대상 사업부는 2024년 매출 약 23억 달러, 영업 EBITA 마진 12.1%, 임직원 약 7,000명 규모였다. (출처: https://www.robotics247.com/article/abb_divests_robotics_division_to_softbank_group_for_5.375b/softbank_robotics)
3. 하드웨어 측면에서 2024~2026년 핵심 신제품은 OmniCore 컨트롤러 기반 대형 로봇(IRB 7710/7720, IRB 6710~6740, 6730S/6750S/6760), 소형 IRB 1010(1.5 kg/370 mm), 신형 IRB 1700/1700ID(2026-10, CIIF), 고속 협동로봇 PoWa(7~30 kg, 5.8 m/s, 2026-04)이다.
4. 소프트웨어 측면은 OmniCore + RobotWare, RobotStudio(AI Assistant 2025-09 / NVIDIA Omniverse 기반 "HyperReality" 2026-03 발표), Wizard Easy Programming, Connected Services(5개 서비스), AMR용 Visual SLAM(Sevensense 인수)이 축이다.
5. IFR World Robotics 2026(2026-09-24): 2025년 글로벌 산업용 로봇 설치 603,307대(+11%), 가동대수 500만 대 돌파, 중국이 354,000대(59%). 한국은 30,000대(-1%)로 4위. (출처: https://ifr.org/ifr-press-releases/news/five-million-robots-now-operate-in-factories-globally)
6. 로봇 밀도(2024년 기준, 2026-04 IFR 발표): 한국 1,220대/만 명으로 세계 1위, 싱가포르 818, 독일 449, 일본 446. (출처: https://www.businesswire.com/news/home/20260408531951/en/Robot-Density-Surges-in-Europe-Asia-and-Americas-IFR-reports)
7. Fanuc FY2025(2026-03 결산) 로봇 부문 매출 3,786억 엔(+15%), Yaskawa FY2025(2026-02 결산) 로보틱스 매출 2,470억 엔(+4.0%)이나 영업이익 -14%, KUKA 2025 매출 38.97억 유로(+4.4%).
8. 중국 로컬 브랜드의 자국 점유율은 2025년 55%(IFR), Estun은 2025년 매출 48.88억 위안(+21.9%)으로 흑자 전환.
9. 협동로봇: Teradyne 로보틱스(UR+MiR) 2025년 매출 3.083억 달러(-15.5%) 후 2026년 2분기 1억 달러(+33%)로 반등. 두산로보틱스 2025년 매출 330억 원(-29.6%), 영업손실 595억 원. 레인보우로보틱스는 2025-02 삼성전자 연결 자회사(지분 35%) 편입.
10. 휴머노이드: Unitree 2025년 5,500대 이상 출하·2025 매출 16.99억 위안, 2026-08 STAR 상장. UBTech 2025년 1,079대 판매. 테슬라는 2026-10-21 Fremont 초기 생산 시작 발표. 한국은 2025-04 K-휴머노이드 연합 출범(2030년까지 1조 원 이상).

---

## TOPIC A. ABB 로보틱스 하드웨어 제품군 (2025~2026)

### A-1. 소형 다관절

| 모델 | 가반하중 | 리치 | 비고 |
|---|---|---|---|
| IRB 1010 | 1.5 kg | 370 mm | ABB 최소형, 풋프린트 135×250 mm, 반복정밀도 0.01 mm, IRB 120 대비 30% 소형 (출처: https://new.abb.com/news/detail/95706/prsrl-abb-unveils-smallest-industrial-robot-with-class-leading-payload-and-accuracy) |
| IRB 1100 | 4 kg | 475 / 580 mm | (출처: https://www.directindustry.com/product-manufacturer/abb-floor-mounted-robot-134806-31750.html) |
| IRB 1200 | 5 / 7 kg | 700 / 900 mm | (출처: 동일) |
| IRB 1300 | 7~12 kg | 900 / 1,150 / 1,400 mm | OmniCore E10 대상 (출처: 동일) |
| IRB 1600 | 6~10 kg | 1.2 / 1.45 m | (출처: https://new.abb.com/products/robotics/robots/articulated-robots) |
| IRB 1700 / 1700ID (신규) | 6~12 kg, 5개 변형 | 미공개 | 2026-10 CIIF 상하이 발표. 사이클타임 최대 20% 단축, 경로 반복정밀도 0.03 mm, 관절속도 700°/s, 풋프린트 50% 축소, 전력 15% 절감, 오일교환 주기 2만 시간. AI 서버랙 조립 등 타깃 (출처: https://www.robotics247.com/article/ciif-2026-abb-robotics-introduces-two-new-robots-for-precision-manufacturing-and-expands-omnicore-eyemotion-with-ai-robot-trainer) |

### A-2. 중형 다관절
- IRB 2600: 8~20 kg, 1.65~2.0 m. IRB 4600: 20~60 kg, 2.05~2.55 m. (출처: https://library.e.abb.com/public/0cc0971903034ce9997a86f05b21be6f/2018%20Product%20Range%20Flyer%20-%20Robots_08.18.pdf)

### A-3. 대형 다관절 (OmniCore 세대)
- IRB 6710/6720/6730/6740: 4개 모델 22개 변형, 150~310 kg, 2.5~3.2 m. 전 세대(IRB 6700, 300 kg/3.2 m, 단종) 대비 에너지 20% 절감·중량 10% 감소, 포즈 반복정밀도 0.03 mm. (출처: https://new.abb.com/products/robotics/robots/articulated-robots/irb-6710 , https://one.robotics.abb.com/Robots/p/IRB-6700)
- IRB 6730S / 6750S(선반형) / IRB 6760(프레스텐딩): 2025-06-24~27 Automatica 뮌헨 데뷔. 선반형 최대 350 kg, OmniCore 경로정밀도 0.9 mm. IRB 6760은 카본파이버 툴링붐으로 분당 15 스트로크(시간당 900파트). 선반형 10대+바닥형 8대 조합 시 15초당 스폿용접 70→80점. (출처: https://new.abb.com/news/detail/127079/prsrl-abb-expands-large-robot-portfolio , https://www.processonline.com.au/content/factory-automation/product/abb-irb-6730s-irb-6750s-and-irb-6760-large-robots-1620844970)
- IRB 7710 / 7720(2024 출시): 합계 16개 변형, 280~620 kg. IRB 7710 최대 500 kg/3.5 m(변형별 2.85~3.5 m), IRB 7720 최대 620 kg/3.5 m(620 kg@2.9 m ~ 450 kg@3.5 m). 기가캐스팅·EV 배터리·주조품·캐빈 핸들링 타깃, 에너지 최대 30% 절감. (출처: https://www.abb.com/global/en/areas/robotics/products/robots/articulated-robots/large-robots/irb-7720 , https://one.robotics.abb.com/en/Robots/p/IRB-7710)
- IRB 7600: 150~500 kg, 2.55~3.5 m. (출처: 2018 Product Range Flyer 상동)
- IRB 8700: 8700-800/3.50(800 kg, 3.5 m) 및 8700-550/4.20(550 kg, 4.2 m), LeanID 옵션. 손목 하향 시 최대 1,000 kg, 반복정밀도 0.05 mm. (출처: https://www.abb.com/global/en/areas/robotics/products/robots/articulated-robots/large-robots/irb-8700)

### A-4. SCARA / 델타
- IRB 920T SCARA: 6 kg, 650 mm, 반복정밀도 0.02 mm. (출처: https://robodk.com/robot/ja/ABB/IRB-920T-6-0-65)
- IRB 360 FlexPicker: 1/3/6/8 kg 변형, 예: 360-8/1130(8 kg, 1,130 mm), 360-6/1600(6 kg, 1,600 mm). (출처: https://library.e.abb.com/public/5089951be174befec1257c430032d757/IRB%20360-Range.pdf)
- IRB 365 FlexPicker: 1.5 kg, 1,100 mm, 5축, 1 kg 제품 기준 분당 120픽(3rd-party 스펙). (출처: https://qviro.com/product/abb/irb-365-flexpicker/alternatives)
- IRB 390 FlexPacker: 1,300 mm 리치, 15 kg(4축)/10 kg(5축), 반복정밀도 0.02 mm. (출처: https://www.abb.com/global/en/areas/robotics/products/robots/delta-robots/irb-390)

### A-5. 도장 로봇
- IRB 5500-27: 7축 컴팩트 도장 로봇, 13 kg, 수직 5,373 mm·수평 4,683 mm(리셀러 스펙), 반복정밀도 0.15 mm. IRB 5510(중형 도장), IRB 5350(도어오프너). (출처: https://www.abb.com/global/en/areas/robotics/products/robots/paint-robots/irb-5500-27 , https://baoanjsc.com.vn/products/painting-robot-IRB-5500-27_801585_en.aspx)
- ABB 가족 페이지 기준 IRB 5500: 13 kg, 2.97 m. (출처: https://one.robotics.abb.com/Robots/p/IRB-5500)

### A-6. 협동로봇

| 모델 | 가반하중 | 리치 | 상태/비고 |
|---|---|---|---|
| YuMi IRB 14000 (양팔) | 0.5 kg/팔 | 0.56 m | 14 DOF, 컨트롤러 포함 38 kg (출처: https://library.e.abb.com/public/544f24358c4d4cfdba7375ad5de30707/9AKK108471A7656_en_A_ABB%20Collaborative%20robotics%20portfolio.pdf) |
| YuMi IRB 14050 (단팔) | 0.5 kg | 0.559 m | 7축, 9.5 kg (출처: https://one.robotics.abb.com/en/robots/p/IRB-14050-YuMi-Single-Arm) |
| GoFa CRB 15000 | 5 / 10 / 12 kg | 0.95 / 1.52 / 1.37 m | 10·12 kg IP67 (출처: https://standardbots.com/blog/gofa-crb-15000 , https://proax.ca/strapiv4/uploads/ABB_OMRON_Robotics_Flyer_208eb5687a.pdf) |
| SWIFTI CRB 1100 | 4 kg | 0.475 / 0.58 m | TCP 5 m/s 초과, 단종·GoFa로 대체 (출처: https://one.robotics.abb.com/Robots/p/CRB-1100) |
| SWIFTI CRB 1300 | 7 / 10 / 11 kg | 0.9~1.4 m | 단종·GoFa로 대체 (출처: https://one.robotics.abb.com/en/robots/p/CRB-1300) |
| PoWa (신규, 2026-04) | 7/10/13/16/20/30 kg | PoWa 7: 0.91 m, 10: 1.52 m, 13: 1.34 m, 16: 1.96 m, 20: 1.67 m, 30: 1.35 m (손목 기준) | 최고속도 5.8 m/s, OmniCore 기반, 개봉 후 1시간 내 가동, 노코드. 머신텐딩·팔레타이징·스크류·아크용접. ABB는 협동로봇 시장 2028년까지 연 20% 성장 전망 (출처: https://www.abb.com/global/en/areas/robotics/products/robots/collaborative-robots/powa , https://www.robotics247.com/article/abb-robotics-launches-powa-cobot-family) |

※ PoWa는 요청서의 "2025"가 아닌 2026-04-24 글로벌 출시 보도이며 Automate 2026 글로벌 프리미어로 소개됐다. (출처: https://www.abb.com/global/en/areas/robotics/events/automate-2026)

### A-7. AMR (ASTI 인수 기반)
- ABB는 2021년 스페인 부르고스 ASTI Mobile Robotics를 약 1.9억 달러에 인수, Flexley 브랜드로 리브랜딩. Flexley Tug(견인 최대 2,000 kg), Flexley Mover(리프팅 최대 1,500 kg). (출처: https://new.abb.com/news/detail/95036/prsrl-abb-rebrands-autonomous-mobile-robot-portfolio , https://vectorshift.ai/research/deals/abb-asti-mobile-robotics-2021)
- Flexley Mover P603(2025-06-26): 1,500 kg급 동급 최소형, Visual SLAM, 위치정밀도 ±5 mm, 인프라 변경 불요, 하중 센싱, AMR Studio 4.0 노코드 플릿 관리, ISO 3691-4/ANSI 56.5. (출처: https://www.abb.com/global/en/news/127073)
- Visual SLAM은 AMR T702V, P604V에 먼저 적용. (출처: https://new.abb.com/news/detail/111398/abb-acquires-sevensense-expanding-leadership-in-next-generation-ai-enabled-mobile-robotics)

---

## TOPIC B. 소프트웨어·제어 생태계

### B-1. OmniCore / IRC5
- OmniCore는 1.7억 달러 이상 투자, 경로정밀도 0.6 mm 미만. (출처: https://new.abb.com/news/detail/116279/abb-launches-next-generation-robotics-control-platform-omnicore)
- C30: 협동로봇·델타·SCARA·IRB 1600급까지. C90XT: IP54, 핫스왑 FlexPendant. (출처: https://www.abb.com/global/en/areas/robotics/products/controllers/omnicore/omnicore-c90xt)
- E10: 19인치 랙마운트, 11 kg 이하(IRB 920T, IRB 1300). V250XT: 300 kg급(IRB 6700 등). IRC5 대비 에너지 최대 20% 절감, RobotWare 기반. (출처: https://new.abb.com/news/detail/85684/prsrl-new-abb-omnicore-robot-controllers-offer-faster-scalable-more-energy-efficient-manufacturing)
- E-Device(Automate 2026): FlexPendant·Windows 태블릿·PC 동일 UX. (출처: https://www.abb.com/global/en/areas/robotics/events/automate-2026)
- IRC5 레거시: SafeMove2가 IRC5 single/compact/paint에 안전 필드버스 추가. (출처: https://www.automate.org/news/abb-expands-collaborative-portfolio-with-the-introduction-of-safemove2-its-latest-generation-robot-monitoring-system)

### B-2. RobotStudio / RAPID / Wizard
- RobotStudio: 가상 컨트롤러가 실제 펌웨어 구동, 사용자 6만 명 이상. (출처: https://www.abb.com/global/en/news/134030/prsrl-abb-robotics-partners-with-nvidia-to-deliver-industrial-grade-physical-ai-at-scale)
- RobotStudio AI Assistant(2025-09-26): 생성형 AI 단계별 가이드, 프리미엄 구독 무상 포함, "Autonomous Versatile Robotics". (출처: https://www.abb.com/global/en/news/129285)
- RobotStudio HyperReality(2026-03-09 발표, 2026 하반기): NVIDIA Omniverse 통합, sim-to-real 갭 최대 99% 해소, 배치비용 최대 40% 절감·출시 50% 단축, Foxconn 파일럿. (출처: https://blogs.nvidia.com/blog/abb-robotics-omniverse , https://www.hpcwire.com/aiwire/2026/03/11/nvidia-and-abb-robotics-combine-simulation-and-ai-to-train-industrial-robots/)
- Wizard Easy Programming: 블록 노코드, 10분 내 티칭, 실시간 RAPID 변환, Skill Creator, 전 OmniCore 지원. (출처: https://www.abb.com/global/en/areas/robotics/products/software/wizard-easy-programming , https://new.abb.com/news/detail/59950/abb-makes-robot-programming-more-intuitive-with-wizard-easy-programming-software)

### B-3. 안전·정밀도·비전·서비스
- SafeMove/SafeMove2: 2008 원조, 2016 2세대. 안전 속도·정지·축범위·자세 감시를 컨트롤러 내부 실행. (출처: https://www.automate.org/news/abb-expands-collaborative-portfolio-with-the-introduction-of-safemove2-its-latest-generation-robot-monitoring-system)
- Absolute Accuracy: 약 0.5 mm 절대정밀도, 레이저트래커 교정. (출처: https://library.e.abb.com/public/0f879113235a0e1dc1257b130056d133/Absolute%20Accuracy%20EN_R4%20US%2002_05.pdf , https://hexagon.com/resources/resource-library/lifelong-absolute-accuracy-industrial-robots)
- Connected Services: 상태감시·진단, 백업관리, 원격접속, 플릿평가, 자산최적화 5종, MyRobot 클라우드. 사고 최대 25% 감소·대응 60% 단축(ABB 주장). (출처: https://www.abb.com/global/en/areas/robotics/services/data-driven-services/connected-services)
- OmniCore EyeMotion + AI Robot Trainer(2026-10 CIIF): 카메라 브랜드 무관, 합성+실제 데이터, 커미셔닝 최대 90%·사이클 50% 단축. (출처: https://www.robotics247.com/article/ciif-2026-abb-robotics-introduces-two-new-robots-for-precision-manufacturing-and-expands-omnicore-eyemotion-with-ai-robot-trainer)
- AI Item Picking: Item Picker 1,400개/h; 2025-03 Fashion Inductor 1,300/h, Parcel Inductor 1,500/h, 정확도 99.5%+. (출처: https://new.abb.com/news/detail/102366/prsrl-abbs-ai-enabled-robotic-item-picker-makes-fulfilment-faster-and-more-efficient , https://www.robotics247.com/article/abb_expands_robotic_item_picking_family_with_ai_powered_functional_modules)
- Microsoft·OpenAI 파트너십은 공식 자료로 확인되지 않음.

### B-4. Sevensense 인수
- ETH 취리히 스핀오프(2021 소수지분 후 인수, 금액 비공개). 커미셔닝 수 주→수 일, Ford·Michelin 적용, 취리히 VSLAM 제품센터. (출처: https://new.abb.com/news/detail/111398/abb-acquires-sevensense-expanding-leadership-in-next-generation-ai-enabled-mobile-robotics , https://www.therobotreport.com/sevensense-acquisition-adds-vslam-smarts-mobile-robots-says-abb/)

### B-5. B&R 관계
- 2019-11 Machine-Centric Robotics: ABB 로봇을 Automation Studio·POWERLINK·OPC UA·openSAFETY에 통합. (출처: https://www.br-automation.com/en/about-us/press-room/abb-and-br-launch-first-fully-integrated-machine-centric-robotics-solution-26-11-2019/)
- 2025 Q4부터 Machine Automation(B&R)은 ABB Automation 사업영역에 편입(매각 대상 아님). (출처: https://www.emr-online.com/abb-q3-2025-results/ , https://library.e.abb.com/public/17c5f84dedb946478c22ba1e00f5673e/ABB-Q4-2025-press-release-English.pdf)

### B-6. 소프트웨어·서비스 매출 전략 및 사업부 규모
- 2025 Q3 콜 기준 TTM 수주 약 22억 달러, 매출 약 24억 달러, 영업 EBITA 약 3억 달러. (출처: https://www.roic.ai/quote/ABBNY/transcripts/2025-year/3-quarter)
- SoftBank는 Marc Segura 체제 독립 법인 운영, AutoStore·Agile Robots·Skild AI와 Physical AI 포트폴리오. (출처: https://group.softbank/en/news/press/20251008)
- 소프트웨어·서비스 매출 비중은 미공시. 분리비용 약 2억 달러, 현금세 4~5억 달러 추정. (출처: https://www.abb.com/global/en/news/129776/abb-to-divest-robotics-division-to-softbank-group)

---

## TOPIC C. 경쟁사 및 산업 트렌드

### C-1. 글로벌 시장 (IFR)
- WR 2026(2026-09-24): 2025년 설치 603,307대(+11%), 가동 500만 대(+9%). 2026 전망 655,000대, 2029 806,000대. 중국 354,000대(+20%, 59%), 로컬 공급 195,000대(+15%), 로컬 점유 55%(2024 57%). 미국 약 38,500대(+12%), 일본 36,219대(-19%), 한국 30,000대(-1%, 4위, 2019년 이후 연 약 31,000대 정체·2027~28 자동차 투자 기대), 독일 25,000대 미만(-8%), 인도 약 10,500대(+15%). (출처: https://ifr.org/ifr-press-releases/news/five-million-robots-now-operate-in-factories-globally , https://ifr.org/img/worldrobotics/Executive_Summary_WR_2026_-_Industrial_Robots.pdf)
- 로봇 밀도(2024): 한국 1,220(연평균 +7%), 싱가포르 818, 독일 449, 일본 446. 중국 166(노동데이터 개정). (출처: https://www.businesswire.com/news/home/20260408531951/en/Robot-Density-Surges-in-Europe-Asia-and-Americas-IFR-reports , https://www.industrial-production-worldwide.com/news/world-robotics-2025-report-reveals-south-korea-singapore-and-germany-have-highest-robot-density)
- 공급사 점유율(Statista, 2023 매출): ABB 13%, Epson 13%, Fanuc 11%, Kawasaki 8%, Yaskawa 8%, KUKA 6%. (출처: https://statista.com/chart/amp/32239/global-market-share-of-industrial-robotics-companies)

### C-2. Big 4 실적
- Fanuc FY2025: 매출 8,578.3억 엔(+7.6%), 순이익 1,665.4억 엔(+12.9%), 로봇 3,786억 엔(약 +15%, 비중 44.1%). FY2026 Q1 매출 2,310억 엔(+17.7%), 영업이익 535억 엔(+26.1%), 연간 전망 9,481억 엔. (출처: https://www.fanuc.co.jp/en/ir/announce/pdf/2026/reference202603_e.pdf , https://www.rttnews.com/3642388/fanuc-fy25-profit-rises-sees-higher-results-in-h1-fy26.aspx?type=ern , https://filingreader.com/news-wire/tokyo/2026-07-31/fanuc-reports-strong-q1-growth-and-raises-forecasts)
- Yaskawa FY2025: 매출 5,421억 엔(+0.8%), 영업이익 473억 엔(-5.7%), 로보틱스 2,470억 엔(+4.0%)·영업이익 204억 엔(-14.0%, 8.3%). FY2026 Q1 매출 1,389.8억 엔(+10.6%), 영업이익 -19.2%, 로봇 영업이익 -82.3%. (출처: https://www.yaskawa-global.com/wp-content/uploads/2026/04/20260410_haifu_en.pdf , https://filingreader.com/news-wire/tokyo/2026-07-10/yaskawa-electric-profit-falls-19-despite-ai-led-revenue-growth)
- KUKA 2025: 수주 41.573억 유로, 매출 38.972억 유로(2024 37.324억), 수주잔고 32.728억 유로, book-to-bill 1.07. 2024 EBIT 7,650만 유로(-51.6%), 순손실 4,350만 유로. (출처: https://www.kuka.com/-/media/kuka-corporate/documents/ir/reports-and-presentations/en/annual-report/annual-report-2025.pdf , https://roboticsandautomationnews.com/2025/05/03/kuka-sinks-into-the-red-with-e43-5-million-loss-triggering-leadership-change-and-strategic-shift/90302/)
- Midea 2025 매출 4,564.52억 위안(+12.11%); 1~3분기 로보틱스·자동화 226억 위안(+9%). (출처: https://www.itiger.com/news/1156101226)

### C-3. 일본 기타
- Epson SCARA 물량 1위, Kawasaki duAro, Denso 자동차 전장, Nachi 중량물. (출처: https://www.evsint.com/de/top-industrial-robot-manufacturers/) 2025~26 신제품 공식 보도는 미확인.

### C-4. 중국
- 로컬 점유율: 2024 1~3분기 51.6%(MIR), 2025 55%(IFR). (출처: https://yicaiglobal.com/news/chinese-industrial-robot-makers-share-of-domestic-market-climbs-to-record-in-first-half)
- Estun 2025: 매출 48.88억 위안(+21.93%), 순이익 4,134만 위안(흑자 전환), 2025 Q1 외자 추월. (출처: https://www1.hkexnews.hk/listedco/listconews/sehk/2026/0330/2026033003426.pdf , https://eu.36kr.com/en/p/3399761971562628)
- Inovance 2위, Siasun·Efort 상위권. (출처: https://www.evsint.com/china-industrial-robot-manufacturers/)
- 가격 압박: 중국 협동로봇 번들 UR 대비 30~40% 저가, Elite EC 약 40% 저가, 2026-04 독일 법원 Elite 가처분. (출처: https://sacra.com/chat/h/050b97c5-671e-46e9-b41f-4ef5cd99f3b8/ , https://mrk-blog.de/en/elite-robots-mit-universal-robots-ur20-pendant/ , https://www.robotics.press/news/universal-robots-competitive-response-cobot-moat/)

### C-5. 협동로봇 업체
- UR/Teradyne: 2025 로보틱스 3.083억 달러(-15.5%), 2025 Q2 UR 6,300만 달러. 2026 Q1 9,100만, Q2 1억 달러(+33%). (출처: https://www.sec.gov/Archives/edgar/data/97210/000119312526059002/ter-20251231.htm , https://www.therobotreport.com/teradyne-robotics-revenue-rises-33-year-over-year-in-q2/)
- 두산로보틱스: 2025 매출 330억 원(-29.6%), 영업손실 595억 원. 2026 Q1 153억, Q2 176.7억(+290%), 북미 51%, 2027 흑자 가이던스. (출처: https://news.bizwatch.co.kr/article/industry/2026/02/11/0039 , https://www.ddaily.co.kr/page/view/2026072417320505230 , https://stock.pstatic.net/stock-research/company/15/20260430_company_275451000.pdf)
- 레인보우로보틱스: 삼성 지분 14.7%→35%, 2025-02-17 연결 편입(잔여 행사 시 58.6%). 2025 매출 약 341억 원(+76.4%), 영업손실 약 25억 원. (출처: https://www.segye.com/newsView/20250102503947 , https://newstomato.com/ReadNews.aspx?no=1249860 , https://www.butler.works/ko/companies/01261644)
- 뉴로메카 2024 매출 252.7억 원, 영업손실 190억 원. HD현대로보틱스 50 kg급 협동로봇 프로토타입(2025-03), HDC 시리즈(Automatica 2025). (출처: https://file.alphasquare.co.kr/media/pdfs/company-report/20250529174457371_12_ko.pdf , https://kidd.co.kr/news/240791)
- Techman 2025 실적 미확인.

### C-6. 휴머노이드 / Physical AI
- Unitree: 2025 매출 16.99억 위안, 휴머노이드 5,500대+, 비중 51.5%, 2026-08 STAR 상장(150.80위안, 약 42억 위안). (출처: https://www.caixinglobal.com/2026-06-02/humanoid-robot-maker-unitree-advances-toward-618-million-shanghai-ipo-102449940.html , https://autonews.gasgoo.com/articles/news/unitree-launches-star-market-ipo-issuance-process-subscriptions-open-august-10-2083181368883253248)
- UBTech: 2025 휴머노이드 8.2억 위안(+2,203%), 1,079대, 그룹 20.01억 위안(+53.3%), Walker S2 2025-11 양산. (출처: https://humanoid.guide/ubtech-humanoid-revenue-jumps-2200-in-2025/ , https://drc.sz.gov.cn/ywb/szxw/tpxw/content/post_12719067.html)
- Tesla Optimus: 2026-10-21 Fremont 초기 생산, 텍사스 건설 중, 외부 납품 2027년 말. 2025 5,000대 계획 90%+ 미달. (출처: https://xenospectrum.com/en/tesla-q3-2026-optimus-profit/ , https://aibusiness.vc/robots/tesla-optimus-production-starts-q3-2026-results-when-you-can-buy-one)
- Figure AI: 2025-09 Series C 10억 달러+, 390억 달러 밸류, 2025 출하 약 150대. (출처: https://seekingalpha.com/news/4495255-figure-raises-1b-in-series-c-hits-39b-valuation-to-scale-humanoid-robot-deployment , https://humanoid.guide/humanoid-deployments-in-2026-favor-figure-and-agility/)
- NVIDIA: CES 2026 GR00T N1.6, GTC 2026(3/18) Physical AI Data Factory·Isaac Teleop GA. (출처: https://techcrunch.com/2026/01/05/nvidia-wants-to-be-the-android-of-generalist-robotics , https://www.storyboard18.com/brand-marketing/nvidia-lays-out-full-stack-push-to-become-the-android-of-general-purpose-robotics-87050.htm)
- SoftBank Physical AI 전략(Skild AI·Agile Robots·AutoStore). (출처: https://www.techrepublic.com/article/news-softbank-acquires-abb-robotics/)

### C-7. 한국 시장·정책
- 2024 로봇산업 실태조사(2025-12): 매출 6조 1,695억 원(+3.2%), 제조업용 3조 1,075억(50.4%), 서비스 1조 800억(17.5%). 2023 5조 9,805억(+1.5%). 2025 기준 조사 2026-11~12 발표 예정. (출처: https://zdnet.co.kr/view/?no=20251229084702 , https://zdnet.co.kr/view/?no=20241222021526 , https://www.irobotnews.com/news/articleView.html?idxno=44544 , https://www.kiria.org/portal/policysut/portalPlcyInquiry.do)
- K-휴머노이드 연합(2025-04): 약 40개 기관, 2030년까지 1조 원+, 6개 전문그룹, 위원장 장병탁, 2028 로봇 AI 파운데이션 모델, 레인보우-CJ대한통운 협력. (출처: https://www.etoday.co.kr/news/view/2460901 , https://www.hellot.net/news/article.html?no=102907 , https://news.tf.co.kr/read/economy/2196200.htm)
- 2026-01-13 피지컬 AI 정책: 산업부 산업인공지능정책관 신설, 2028 자립 플랫폼·모델, 2030 가사·돌봄 휴머노이드, 기계연 2026-12 K-AI 휴머노이드 V1. 과기정통부 K-문샷 로드맵(안) 2026-08. (출처: https://v.daum.net/v/20260113115410967 , https://www.khan.co.kr/article/202603051154001)
- 기획예산처 2026-07 국가제조데이터라이브러리·2027 예산 추진. (출처: https://v.daum.net/v/20260609141647154)

---

## 부록: 확인 불가·주의 항목
- ABB 로보틱스 2025 연간 확정 매출·수주 미공개(TTM 약 24억 달러만 확인).
- IRB 7710 ABB 공식 페이지 간 수치 상이(500 kg/3.5 m vs 280~420 kg/2.5~3.2 m).
- GoFa 10 리치: ABB 1.62 m(TCP) vs 3rd-party 1.52 m.
- Flexley T702 스펙, Techman 2025, Microsoft/OpenAI-ABB, 2025 Big 4 공식 점유율 미확인.
- PoWa는 2026-04 출시(요청서 "2025" 아님).
