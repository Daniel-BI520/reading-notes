#!/usr/bin/env python3
"""Add 原书金句 section to all 13 book essence pages."""

import re
import os

BOOKS_DIR = '/app/data/所有对话/主对话/gh-publish/books'

# ===========================================================================
# Golden quotes for each book (curated from report pages)
# Each entry: list of 8-12 quotes per book
# ===========================================================================

BOOK_QUOTES = {
    'book_001_tech_product_marketing.html': [
        '构建产品的认知，与构建产品本身同等重要，有时甚至更重要。',
        '没有被讲述的价值，就等于不存在。',
        '产品的价值不是客观存在的，而是通过叙事建构的。',
        '你自己说的话最不重要，别人替你说的话才最重要。',
        '产品战略的思考顺序是"什么—如何—为什么—何时"，但GTM战略把"何时"放在第一位。',
        '定位是长期游戏，信息传递是短期游戏。',
        '唯一能在全球规模化增长的方式，就是确保有其他人替你布道。',
        '定价不是关于生产成本，它关乎人们对产品的感知价值和支付意愿。',
        '品牌不是logo和口号，品牌是客户与公司之间的承诺。',
        'PGTM画布的本质不是规划工具，而是组织共识工具。',
    ],

    'book_002_industry_research.html': [
        '行业研究永远是概率性的，不是确定性的。',
        '选择比努力更重要——资源配置的效率，远大于资源投入的数量。',
        '本书真正的创新，在于"串联"——用产业生命周期这条主线，把原本各自为政的分析维度串起来。',
        '把横轴从"时间"换成"渗透率"——这是理解产业生命周期的钥匙。',
        '每个阶段有每个阶段的核心命题，每个分析维度都服务于一个特定的核心命题。',
        '通过独占生产要素形成资源垄断护城河，通过独占生产关系形成网络效应护城河。',
        '商学院课本上的知识跟产业界的实际应用之间，存在一条鸿沟。',
        '可行性是早期行业的核心命题，规模性是成长期的核心命题，防守性是成熟期的核心命题。',
        '行业研究的本质，是在不确定性中寻找确定性的概率优势。',
        '先判断行业处在哪个阶段，然后聚焦这个阶段的核心命题，用对应的分析工具深入下去。',
    ],

    'book_003_finance_dc_network.html': [
        'IPO模型本质上是网络架构的"分层抽象方法论"——每一层只关心本层的能力提供和向上层的接口定义。',
        '六大通用属性看似是架构的"边角料"，实则是金融网络能否真正满足业务SLA的关键。',
        '从物理与逻辑解耦开始，金融数据中心网络从烟囱式架构走向虚拟化架构。',
        '细节决定成败——QoS设计直接决定交易高峰期核心业务的体验。',
        '分层解耦的设计原则：一个好的方案应该是分层清晰、接口明确的，每一层都可以独立演进。',
        'Fabric是数据中心网络的核心构件，规模设计、接入设计、分区定制缺一不可。',
        '多地多中心布局是金融级高可用的必然选择，DCI互联是关键技术挑战。',
        '安全不是事后补丁，而是从架构设计之初就要嵌入的基本属性。',
        '从传统运维向SDN运维、再向AIOps智能运维演进，是数据中心运维的必然路径。',
        'AI Fabric、IDN、MESH²——下一代数据中心网络的三大前沿方向。',
    ],

    'book_004_hassabis_deepmind.html': [
        '顶尖人才的早期经历往往定义了其思维范式。',
        '第一性原理思维不是口号——从最基本的判断出发，推导出事物的终极意义。',
        '讲故事的天赋与自我欺骗的风险之间，只有一条微妙的界限。',
        '顶尖团队的战斗力来自能力互补，而不是技能重叠。',
        '只招信徒——在前沿技术领域，相信使命的人比只看薪资的人产出高得多。',
        '真正的技术突破往往来自跨领域的组合创新。',
        '选择合作伙伴时，不仅要看出价，更要看对方是否真正理解你所做事情的价值。',
        '最好的谈判不是围绕价格，而是围绕价值。',
        '技术落地的最大障碍往往不是技术本身，而是信任。',
        '你的核心优势也可能是你的盲区——最危险的不是你不知道的东西，而是你以为自己知道、但其实错了的东西。',
        '理想主义必须与现实主义结合。',
    ],

    'book_005_singularity_nearer.html': [
        '技术进步呈指数级增长，人类正处于加速曲线最陡峭的"冲刺阶段"。',
        '指数增长的"膝盖弯"已经拐过——前99天只覆盖了水面的1%，但第100天就铺满了整个池塘。',
        '进化是一个信息处理能力不断升级的过程，每一次范式跃迁都让信息的存储、传输、处理效率提升几个数量级。',
        '奇点不是凭空出现的"神迹"，而是138亿年进化曲线自然延伸的结果。',
        '基因技术、纳米技术、人工智能三大领域互相赋能交叉渗透，形成"1+1+1>3"的协同加速效应。',
        '战略规划的时间窗口正在从"十年规划"压缩到"三年迭代"。',
        '人类的直觉天然习惯线性思维，但技术的进步是指数级的。',
        '2022年大模型落地标志着第五纪元（人机融合纪元）的正式开启。',
        '不要孤立地看待某一项技术趋势，要看到不同技术领域之间的交叉融合效应。',
        '加速回报定律从摩尔定律拓展为覆盖宇宙演化、生物DNA、全部信息科技的普适进化规律。',
    ],

    'book_006_chip_history.html': [
        '芯片是人类有史以来最复杂的制造物，也是现代文明的基石。',
        '从晶体管到集成电路，从微处理器到SoC——每一次范式跃迁都让算力提升几个数量级。',
        '摩尔定律不是物理定律，而是人类创新能力的宣言。',
        '芯片发展史不是线性的技术进步史，而是"危机—突破—新危机—再突破"的螺旋上升史。',
        '每一次芯片架构的变革，都伴随着整个IT产业格局的重新洗牌。',
        '光刻技术是芯片制造皇冠上的明珠，也是最精密的人类制造工艺。',
        '芯片产业的全球分工是效率最优的选择，也是地缘政治博弈的焦点。',
        '从专用到通用、再从通用到专用——芯片架构的钟摆效应从未停止。',
        '芯片是底层基础设施中的基础设施，它的发展速度决定了整个信息产业的发展速度。',
        '理解芯片史，才能真正理解为什么"算力就是生产力"。',
    ],

    'book_007_zero_trust.html': [
        '边界安全模型试图把攻击者阻挡在可信的内部网络之外，然而零信任模型认识到这种方法注定会失败。',
        '网络无时无刻不处于危险的环境中——这是零信任的第一假定。',
        '网络的位置不足以决定网络的可信程度。',
        '所有的设备、用户和网络流量都应当经过认证和授权。',
        '安全策略必须是动态的，并基于尽可能多的数据来计算信任。',
        '最小特权原则：一个实体应该只被授予完成任务所需要的特权，而不是被授予该实体想要得到的权限。',
        '问题的根源不是防火墙不够强，而是信任的锚点错了。',
        '零信任不是要换掉现有的防火墙，而是在现有安全体系之上，加一层以身份为核心的精细访问控制。',
        '零信任落地不需要一步到位——先摸清家底，再建身份底座，最后逐步推进精细化控制。',
        '从"假设安全"到"假设危险"，从"位置信任"到"身份信任"，从"静态防御"到"动态演进"——这是思维方式的根本转变。',
        '全球七成以上的数据泄露发生在内网横向移动阶段。',
    ],

    'book_008_cloud_dc_network.html': [
        '技术的成功不仅取决于技术本身的优劣，更取决于演进成本和生态支持。',
        '大数据需要大管道——这是数据中心网络变革的第一驱动力。',
        '应用架构的微服务化，使得东西向流量爆发式增长。',
        '攻击面从边界转向内部——超过75%的数据中心流量是东西向的。',
        '从传统三层架构到Spine-Leaf扁平架构，是数据中心网络的一次范式革命。',
        'VXLAN凭借"在三层IP网上构建虚拟二层"的思路，成为了业界的标准选择。',
        'EVPN为VXLAN带来了控制面——自动发现、控制面学习、广播抑制三大核心价值。',
        '集中式网关到分布式网关的演进，解决了VXLAN性能瓶颈和单点故障问题。',
        '自动驾驶网络是数据中心网络的终极目标——管理、控制、分析、优化全由AI驱动。',
        '每一分钟的停机都可能对应数十万甚至数百万的经济损失，以及难以估量的声誉影响。',
    ],

    'book_009_private_cloud.html': [
        '"规划先行"是私有云项目成功的关键保障。',
        '虚拟化的本质是资源池化——提高资源利用率、简化运维管理。',
        '第一次跃迁是从"资源管理"到"服务管理"——从管理员驱动的人工操作模式，到自助服务的服务化交付模式。',
        '数据主权与合规可控是私有云最核心的价值主张。',
        '性能专属与稳定保障是核心业务系统选择私有云的关键因素。',
        '混合云架构的核心枢纽是私有云——"数据在私、计算在公"。',
        '稳定性是压倒一切的首要考虑因素——一次意外的宕机可能造成数百万的经济损失。',
        '私有云网络规划的核心原则是"三网隔离"——管理网络、业务网络、存储网络必须隔离。',
        '为什么三网隔离如此重要？根本原因在于避免流量争抢。',
        'vMotion、DRS、HA、FT——集群调度是vCenter最核心的价值所在。',
        '行业方案的设计需要跨界融合——"云网端"一体化是提升方案价值的重要方向。',
    ],

    'book_010_cloud_primer.html': [
        '云计算说穿了就是IT资源的社会化分工——云计算就是IT领域的"自来水厂"。',
        '云计算不是一种新的计算技术，而是一种新的计算模式。',
        '计算设备和输入/输出设备的分离是云计算的特征之一。',
        '这个分离的本质是专业化分工——企业只需要关注自己的核心业务。',
        '任何一项技术的出现，都是为了解决一个具体的问题；不理解问题，就不可能真正理解技术。',
        '虚拟化就好比把一个大房子用墙隔成很多个小房间——既保持高资源利用率，又维持良好的隔离性。',
        '一个云计算中心的延时半径通常为100毫秒——与地理位置没有直接关系，而与网络路径上的转发机构和数目有关。',
        '读透云计算的来龙去脉，讲清技术背后的前因后果，把每一个概念都转化成客户能听懂的语言——这就是售前工程师的核心竞争力。',
        '云原生，就是根据云的特点专门定制应用——真正享受云带来的好处。',
        '传统的应用上云，就像把老家具原封不动搬到新房子里；云原生，是根据新房子的户型专门定制家具。',
    ],

    'book_011_salesforce_legend.html': [
        '不要打折，不要降低早期产品的价值。',
        '战略的本质是清晰和聚焦——V2MOM写在信封背面就够了。',
        '价值观不是一堆好词的堆砌，而是决策的优先级排序。',
        'V2MOM的核心力量不在于五个问题本身，而在于级联和透明两个机制。',
        '客户嫌贵往往不是因为价格本身，而是因为他没有看到足够的价值——你越降价，他就越觉得你的产品不值钱。',
        'SaaS模式是成立的——客户确实愿意为在线软件持续付费。',
        '客户信任是硬通货——在最困难的时候，是客户的信任让公司活了下来。',
        'No Software不仅是一句口号，它是一整套商业模式、企业文化和用户体验的革命。',
        'Parker Harris从第一天就坚持的多租户元数据架构，是SaaS模式、平台化战略、生态系统三者共同的技术地基。',
        '伟大的创意往往诞生于放松的时刻——与海豚共泳的那一刻，贝尼奥夫获得了创办Salesforce的灵感。',
        '价格谈判中最容易犯的错误就是一遇到阻力就降价，好像降价是解决一切问题的万能钥匙。',
    ],

    'book_012_segmentation_blueprint.html': [
        '分段失败的根因在组织不在技术——70%以上的分段项目半途而废，不是因为技术选型错误，而是因为组织性障碍。',
        '身份是现代分段的核心锚点——只有以身份为核心编排策略，才能在混合云、移动办公、IoT爆发的环境中保持一致性。',
        '传统分段基于IP拓扑，零信任时代的分段必须以身份为核心。',
        '策略与治理、身份、漏洞管理、执行、分析——零信任五支柱是分段的指导框架。',
        '分段不是一上来就搞微分段，而是从业务对齐开始，循序渐进地推进。',
        '为什么分段策略会失败？很重要的一个原因就是团队没有对齐业务目标。',
        '从传统VLAN到微分段、再到纳秒分段——分段技术在持续演进，但核心原则始终不变。',
        '防火墙是安全的基础设备，但防火墙和分段不是一回事。',
        '基于业务对齐的渐进式分段实施路径，填补了"知道要分段但不知道怎么分段"的行业实践空白。',
        '很多厂商一上来就给客户推最复杂的微分段，但实际上大多数客户根本用不到那个程度。',
    ],

    'book_013_erqiannianjian.html': [
        '任何组织都有"专制化"的天然倾向。',
        '资源集中是所有系统的天然趋势，从土地到市场份额都是如此。',
        '大公司的"官僚化"是必然趋势，关键是识别并应对。',
        '企业也有生命周期，规律和王朝周期律惊人相似。',
        '底层的反抗永远是推动变革的终极力量，但底层造反的成功率极低。',
        '每个组织里都有"外戚"和"宦官"——那些不靠能力、而靠关系上位的人。',
        '做方案就像打天下——"打下来"只是第一步，"守住"才是真正的考验。',
        '卖产品的下策是卖功能（暴力），上策是卖理念（意识形态）。',
        '大公司的"流程化"和宋代的"文官制度"是一回事——提高了稳定性，降低了战斗力。',
        '当一个公司"一言堂"太严重时，要小心——可能是"顶峰"，也可能是"末路"。',
        '企业变革的成功率很低，原因和历史上的变法失败如出一辙。',
    ],
}

# ===========================================================================
# Insertion points for each book (what to find, where to insert before/after)
# Format: (find_pattern, position)
# position: 'after' = insert after the found section, 'before' = insert before
# ===========================================================================

INSERTION_POINTS = {
    'book_001_tech_product_marketing.html': {
        # Page-style: insert after "核心观点深度提炼" page, before "五大售前落地方法（上）"
        'type': 'page-style',
        'before_pattern': r'<!-- ========== 第4页：五大落地方法（上） ========== -->',
        'theme_color': '#3b82f6',
        'section_color_before': '#1a56db',
    },
    'book_002_industry_research.html': {
        # Web-style: insert after summary-card, before first h2 section
        'type': 'web-style',
        'before_pattern': r'  <h2>一、书籍核心框架与方法论</h2>',
        'theme_color': '#7c3aed',
        'section_color_before': '#5b21b6',
    },
    'book_003_finance_dc_network.html': {
        'type': 'web-style',
        'before_pattern': r'  <h2>一、全书脉络与核心逻辑</h2>',
        'theme_color': '#d97706',
        'section_color_before': '#92400e',
    },
    'book_004_hassabis_deepmind.html': {
        'type': 'web-style',
        'before_pattern': r'  <h2>一、DeepMind里程碑时间线</h2>',
        'theme_color': '#0ea5e9',
        'section_color_before': '#0369a1',
    },
    'book_005_singularity_nearer.html': {
        'type': 'web-style',
        'before_pattern': r'<h2 class="section-title">📖 章节精要</h2>',
        'theme_color': '#7c3aed',
        'section_color_before': '#5b21b6',
    },
    'book_006_chip_history.html': {
        'type': 'web-style',
        'before_pattern': r'<h2 class="section-title">📅 芯片发展史七大转折点',
        'theme_color': '#f97316',
        'section_color_before': '#c2410c',
    },
    'book_007_zero_trust.html': {
        'type': 'web-style',
        'before_pattern': r'<h2 class="section-title">⚔️ 范式对比',
        'theme_color': '#10b981',
        'section_color_before': '#047857',
    },
    'book_008_cloud_dc_network.html': {
        'type': 'web-style',
        'before_pattern': r'<h2 class="section-title">🏗️ 技术体系概览</h2>',
        'theme_color': '#0ea5e9',
        'section_color_before': '#0369a1',
    },
    'book_009_private_cloud.html': {
        'type': 'web-style',
        'before_pattern': r'<h2 class="section-title">🏗️ 技术体系概览</h2>',
        'theme_color': '#3b82f6',
        'section_color_before': '#1d4ed8',
    },
    'book_010_cloud_primer.html': {
        'type': 'web-style',
        'before_pattern': r'<h2 class="section-title">🏗️ 技术体系概览</h2>',
        'theme_color': '#f97316',
        'section_color_before': '#c2410c',
    },
    'book_011_salesforce_legend.html': {
        'type': 'web-style',
        'before_pattern': r'<h2 class="section-title">📈 从0到千亿美元的因果链条</h2>',
        'theme_color': '#0d6efd',
        'section_color_before': '#0a58ca',
    },
    'book_012_segmentation_blueprint.html': {
        'type': 'web-style',
        'before_pattern': r'<h2 class="section-title">🔑 核心概念精选</h2>',
        'theme_color': '#10b981',
        'section_color_before': '#047857',
    },
    'book_013_erqiannianjian.html': {
        'type': 'web-style',
        'before_pattern': r'<h2 class="section-title">🏛️ 全书知识骨架</h2>',
        'theme_color': '#b45309',
        'section_color_before': '#78350f',
    },
}

# ===========================================================================
# Generate HTML for the golden quotes section
# ===========================================================================

def generate_web_style_quotes_section(quotes, theme_color):
    """Generate web-style golden quotes section HTML."""
    # Generate quote items
    quote_items = ''
    for i, quote in enumerate(quotes, 1):
        quote_items += f'''        <div class="golden-quote-item">
          <div class="golden-quote-num">{i}</div>
          <div class="golden-quote-text">{quote}</div>
        </div>
'''
    
    html = f'''
  <!-- 原书金句 -->
  <div class="section golden-quotes-section">
    <h2 class="section-title">💎 原书金句</h2>
    <p class="section-desc">书中最有价值的核心观点与论断，值得反复品味。</p>
    <div class="golden-quotes-grid">
{quote_items.rstrip()}
    </div>
  </div>
'''
    
    # CSS styles
    css = f'''
  /* 原书金句板块 */
  .golden-quotes-section {{
    margin-bottom: 40px;
  }}
  .section-desc {{
    color: var(--text-secondary);
    font-size: 14px;
    margin-bottom: 20px;
    padding-left: 4px;
  }}
  .golden-quotes-grid {{
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 14px;
  }}
  .golden-quote-item {{
    background: linear-gradient(135deg, {theme_color}10, {theme_color}18);
    border-left: 4px solid {theme_color};
    border-radius: 0 10px 10px 0;
    padding: 14px 16px 14px 18px;
    display: flex;
    gap: 12px;
    align-items: flex-start;
    transition: all 0.25s ease;
  }}
  .golden-quote-item:hover {{
    transform: translateY(-2px);
    box-shadow: 0 6px 20px {theme_color}22;
    background: linear-gradient(135deg, {theme_color}18, {theme_color}25);
  }}
  .golden-quote-num {{
    width: 26px;
    height: 26px;
    min-width: 26px;
    background: linear-gradient(135deg, {theme_color}, {theme_color}dd);
    color: white;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 13px;
    font-weight: 700;
    flex-shrink: 0;
    margin-top: 1px;
  }}
  .golden-quote-text {{
    font-size: 13.5px;
    line-height: 1.75;
    color: var(--text);
    font-weight: 500;
  }}
  @media (max-width: 768px) {{
    .golden-quotes-grid {{
      grid-template-columns: 1fr;
    }}
  }}
'''
    
    return html, css


def generate_page_style_quotes_section(quotes, theme_color, page_num, total_pages):
    """Generate page-style golden quotes section (a full page)."""
    quote_blocks = ''
    for i, quote in enumerate(quotes, 1):
        quote_blocks += f'''  <div class="golden-quote-card">
    <div class="golden-quote-index">❶</div>
    <div class="golden-quote-content">{quote}</div>
  </div>
'''
    # Use circled numbers for visual appeal
    circled = ['❶','❷','❸','❹','❺','❻','❼','❽','❾','❶⓿','⓫','⓬']
    
    quote_blocks = ''
    for i, quote in enumerate(quotes):
        num = circled[i] if i < len(circled) else f'{i+1}.'
        quote_blocks += f'''  <div class="golden-quote-box">
    <p><strong style="color: {theme_color};">{num}</strong> {quote}</p>
  </div>
'''
    
    html = f'''
<!-- ========== 第{page_num}页：原书金句 ========== -->
<div class="page">
  <div class="section-title">💎 原书金句</div>
  <div class="section-en">ORIGINAL BOOK GOLDEN QUOTES</div>

  <p style="margin-bottom: 14px; color: #64748b; font-size: 12.5px;">
    书中最具冲击力的核心观点与论断，共{len(quotes)}条，值得反复品味、单独引用。
  </p>

{quote_blocks.rstrip()}

  <div class="page-footer">
    <span class="page-tag">— {page_num} / {total_pages} —</span>
  </div>
</div>
'''
    
    css = f'''
  /* 原书金句卡片 */
  .golden-quote-box {{
    background: linear-gradient(135deg, #f8fafc, {theme_color}08);
    border-left: 4px solid {theme_color};
    border-radius: 0 8px 8px 0;
    padding: 10px 16px 10px 16px;
    margin-bottom: 10px;
    transition: all 0.2s;
  }}
  .golden-quote-box:hover {{
    background: linear-gradient(135deg, {theme_color}08, {theme_color}12);
    transform: translateX(2px);
  }}
  .golden-quote-box p {{
    margin-bottom: 0;
    font-size: 13px;
    line-height: 1.75;
    color: #1e293b;
  }}
'''
    
    return html, css


# ===========================================================================
# Main processing function
# ===========================================================================

def process_book(book_file):
    """Process a single book page."""
    filepath = os.path.join(BOOKS_DIR, book_file)
    
    if book_file not in BOOK_QUOTES:
        print(f'  SKIP: No quotes defined for {book_file}')
        return False
    
    if book_file not in INSERTION_POINTS:
        print(f'  SKIP: No insertion point defined for {book_file}')
        return False
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check if already has golden quotes section
    if '原书金句' in content and 'golden-quotes' in content:
        print(f'  SKIP: Already has golden quotes section')
        return False
    
    quotes = BOOK_QUOTES[book_file]
    point = INSERTION_POINTS[book_file]
    theme_color = point['theme_color']
    
    if point['type'] == 'web-style':
        section_html, section_css = generate_web_style_quotes_section(quotes, theme_color)
        
        # Insert CSS before </style>
        css_insert_pos = content.rfind('</style>')
        if css_insert_pos == -1:
            print(f'  ERROR: Could not find </style> tag')
            return False
        content = content[:css_insert_pos] + section_css + '\n' + content[css_insert_pos:]
        
        # Insert HTML before the target section
        before_pattern = point['before_pattern']
        match = re.search(before_pattern, content)
        if not match:
            print(f'  ERROR: Could not find insertion pattern: {before_pattern[:50]}')
            return False
        
        insert_pos = match.start()
        content = content[:insert_pos] + section_html + '\n' + content[insert_pos:]
        
    elif point['type'] == 'page-style':
        # For page-style, we need to insert a new page and update page numbers
        section_html, section_css = generate_page_style_quotes_section(
            quotes, theme_color, page_num=4, total_pages=9  # Will be updated
        )
        
        # Insert CSS before </style>
        css_insert_pos = content.rfind('</style>')
        if css_insert_pos == -1:
            print(f'  ERROR: Could not find </style> tag')
            return False
        content = content[:css_insert_pos] + section_css + '\n' + content[css_insert_pos:]
        
        # Insert the new page before the target
        before_pattern = point['before_pattern']
        match = re.search(before_pattern, content)
        if not match:
            print(f'  ERROR: Could not find insertion pattern')
            return False
        
        insert_pos = match.start()
        content = content[:insert_pos] + section_html + '\n' + content[insert_pos:]
        
        # Update page numbers (pages after insertion shift by 1)
        # Find all page tags and renumber
        total_pages = 9  # original 8 + 1 new page
        content = re.sub(
            r'— (\d+) / 8 —',
            lambda m: f'— {int(m.group(1)) + 1 if int(m.group(1)) >= 4 else m.group(1)} / {total_pages} —',
            content
        )
        # Also fix the 第X页 in comments
        content = re.sub(
            r'第(\d+)页：五大落地方法',
            lambda m: f'第{int(m.group(1)) + 1}页：五大落地方法',
            content
        )
        # Fix subsequent pages
        for old_page, new_page in [(4, 5), (5, 6), (6, 7), (7, 8), (8, 9)]:
            content = content.replace(
                f'第{old_page}页',
                f'第{new_page}页',
                1
            ) if f'第{old_page}页' in content and old_page >= 4 else content
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f'  OK: Added {len(quotes)} golden quotes')
    return True


# ===========================================================================
# Run
# ===========================================================================

if __name__ == '__main__':
    print('Processing 13 books...')
    print('=' * 50)
    
    success = 0
    total = 0
    
    for book_file in sorted(BOOK_QUOTES.keys()):
        total += 1
        print(f'\n[{total:2d}/13] {book_file}')
        if process_book(book_file):
            success += 1
    
    print('\n' + '=' * 50)
    print(f'Done: {success}/{total} books processed successfully')

