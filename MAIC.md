# **From MOOC to MAIC: Reshaping Online Teaching and Learning through LLM-driven Agents** 

**Jifan Yu**<sup>1</sup> **, Zheyuan Zhang**<sup>2</sup> **, Daniel Zhang-li**<sup>2</sup> **, Shangqing Tu**<sup>2</sup> **, Zhanxin Hao**<sup>1</sup> **, Ruimiao Li**<sup>1</sup> **, Haoxuan Li**<sup>2</sup> **, Yuanchun Wang, Hanming Li**<sup>2</sup> **, Linlu Gong**<sup>2</sup> **, Jie Cao**<sup>1</sup> **, Jiayin Lin**<sup>2</sup> **, Jinchang Zhou**<sup>2</sup> **, Fei Qin**<sup>1</sup> **, Haohua Wang**<sup>2</sup> **, Jianxiao Jiang**<sup>1</sup> **, Lijun Deng**<sup>2</sup> **, Yisi Zhan**<sup>1</sup> **, Chaojun Xiao**<sup>2</sup> **, Xusheng Dai**<sup>2</sup> **, Xuan Yan**<sup>2</sup> **, Nianyi Lin**<sup>1</sup> **, Nan Zhang**<sup>3</sup> **, Ruixin Ni**<sup>3</sup> **, Yang Dang**<sup>1</sup> **, Lei Hou**<sup>2</sup> **, Yu Zhang**<sup>1</sup> **, Xu Han**<sup>2</sup> **,** 

**Manli Li**<sup>1</sup> **, Juanzi Li**<sup>2</sup> **, Zhiyuan Liu**<sup>2</sup><sup>_∗_</sup> **, Huiqin Liu**<sup>1</sup><sup>_∗_</sup> **, Maosong Sun**<sup>2</sup><sup>_∗_</sup> 

1Institute of Education, Tsinghua University. 

2Department of Computer Science and Technology, Tsinghua University. 

3ModelBest Inc. 

```
thu_maic@tsinghua.edu.cn
```

## **Abstract** 

Since the first instances of online education, where courses were uploaded to accessible and shared online platforms, this form of scaling the dissemination of human knowledge to reach a broader audience has sparked extensive discussion and widespread adoption. Recognizing that personalized learning still holds significant potential for improvement, new AI technologies have been continuously integrated into this learning format, resulting in a variety of educational AI applications such as educational recommendation and intelligent tutoring. The emergence of intelligence in large language models (LLMs) has allowed for these educational enhancements to be built upon a unified foundational model, enabling deeper integration. In this context, we propose MAIC (Massive AI-empowered Course), a new form of online education that leverages LLM-driven multi-agent systems to construct an AI-augmented classroom, balancing scalability with adaptivity. Beyond exploring the conceptual framework and technical innovations, we conduct preliminary experiments at Tsinghua University, one of China’s leading universities. Drawing from over 100 _,_ 000 learning records of more than 500 students<sup>2</sup> , we obtain a series of valuable observations and initial analyses. This project will continue to evolve, ultimately aiming to establish a comprehensive open platform that supports and unifies research, technology, and applications in exploring the possibilities of online education in the era of large model AI. We envision this platform as a collaborative hub, bringing together educators, researchers, and innovators to collectively explore the future of AI-driven online education. 

## **1 Introduction** 

**Explicit Background: Evolution for** **_Scalability_** . The evolution of online education stands as a testament to humanity’s relentless pursuit of knowledge, transcending the limitations of time and space (Koller and Ng, 2013). From the humble beginnings of oral tradition to the advent of the printed book (Froebel, 1886; Halstead and Taylor, 2005), education has continually sought ways to expand its reach. Yet, for centuries, the traditional model of education was bound by the constraints of physical classrooms, limited resources, and localized instruction. The dawn of the internet marked 

> _∗_ Corresponding Authors. 

> 2We follow the approval from Tsinghua University Sci.&Tech. Ethics Committee (NO.THU-04-2024-56). 

Preprint. Under review. 



<!-- Start of picture text -->
MOOC MAIC<br>$ 25,000  to make a course Less than $ 2 and 30 min per course<br>60 hours  Personalize: Read:<br>customize the course construct teaching agenda and KB<br>Preparing Designing Writing Scripts course description<br>course objective<br>Teach Course Content Creation teaching style<br>Video Creation Slides Textbooks<br>Teacher<br>Teacher Video Exercises Videos<br>Recording Editing Upload: Plan:<br>upload materials generate functions and agents<br>Teacher Agent Classmate Agents<br>Today, let's talk about Wow! If there are plenty<br>Watching Large Language Models We know talked that they . of data,  know  there relation to how can we<br>MOOC Videos learn from a massive certain abilities? Can<br>amount of data, but ... you explain more?<br>Students Video<br>Learn Student DoingQuiz Exercises MentoringOffline Teacher Let's do What is the first stage totrain an LLM?A. Pre-training;  B. SFT; C. Instruction tuning; D. RLHF a little quiz ! Student Based on your quizresults, I to improve by learningsome prerequisitecourses, such as ... suggest  you<br>Assistant Agent Analyzer Agent<br>1 Video for N Students  N Agents for 1 Student<br><!-- End of picture text -->

Figure 1: MOOC V.S. MAIC from the aspects of teaching and learning. 

a revolutionary shift, heralding the age of online education, where the dream of universal access to knowledge began to take tangible form. Specifically, the Massive Open Online Course (MOOC) phenomenon marks a significant milestone in the evolution of online education, reflecting both technological advancement and educational innovation (Cormier, 2008; Daniel, 2012). Since then, platforms like edX<sup>3</sup> , involving institutions such as MIT and Harvard, and Coursera<sup>4</sup> , originating from Stanford, have integrated learning resources from over 270 renowned universities (Pappano, 2012; Papadakis, 2023). These platforms have attracted more than 100 million learners globally, progressively realizing the **_Scalability_** of online education. 

**Implicit Motivation: Determination of** **_Adaptivity_** . However, this paradigm of serving thousands of learners from diverse backgrounds through one pre-recorded video (Reich and Ruipérez-Valiente, 2019) (as shown in Figure 1) struggles to align with the educational philosophy of “teaching in accordance with individual aptitudes” (Reich, 2015; Zhu et al., 2020). This challenge has become a significant reason for the subsequent efforts that introducing of AI techniques into online learning. To achieve the **_Adaptivity_** of learning, a series of tasks such as learning path planning (Nabizadeh et al., 2020; Zhong et al., 2022), course recommendation (Jiang et al., 2019b; Zhang et al., 2018; Jing and Tang, 2017), and intelligent tutoring (Yilmaz et al., 2022; Tu et al., 2023)—driven by technologies like recommendation systems and dialogue generation—have been employed to enhance the student learning experience. 

Although these technologies have been applied across various aspects of teaching and learning, the significant differences among the supporting tasks before, during, and after instruction have posed challenges for unifying them under a single deep learning framework (Kabudi et al., 2021). Such fragmentation has, in part, delayed the emergence of a new platform where AI and online learning are fully integrated. However, with the rapid advancement of generative AI (Epstein et al., 2023), large language models (LLMs) have created fresh opportunities for AI-powered learning paradigms. Models such as GPT-4 (Achiam et al., 2023) and LLaMA (Touvron et al., 2023) possess strong generalization capabilities and encapsulate vast parametric knowledge, allowing for the flexible configuration of intelligent agents (Chen et al., 2023) built upon them. Currently, LLM-driven multi-agent systems (Wu et al., 2023) have already been explored for applications such as social simulation (Park et al., 2023a) and the execution of complex tasks like software development (Qian et al., 2023). This progress opens up a potential pathway for introducing large language model multi-agent systems to create entirely new online teaching and learning experiences. 

> 3 `https://www.edx.org/` 

> 4 `https://www.coursera.org/` 

2 

**Proposal of MAIC** . At the critical juncture of a new era defined by large language models and multi-agent systems in online education, we introduce MAIC (Massive AI-empowered Course). MAIC is dedicated to exploring the integration of multi-agent systems across various stages of online learning, including course preparation, instruction, and analysis, with the goal of balancing **_Scalability_** and **_Adaptivity_** of online education. The core concept of MAIC is to construct a series of LLM-driven agents to support both **Teaching** and **Learning** in the online educational environment. As illustrated in the Figure 1, the paradigm of MOOC and MAIC can be featured with two primary aspects: 

**Teaching** : This action is primarily performed by the instructor. In previous MOOC, the instructor is responsible for thoroughly preparing course materials, drafting lecture notes, and spending considerable time meticulously recording the course. The final output typically consists of a series of pre-recorded instructional videos. For the proposed MAIC, however, the instructor only needs to upload the teaching slides. With intelligent assistance, the instructor can further complete the PPT creation, after which the agents, utilizing a range of models such as multimodal understanding and knowledge structure extraction, will generate structured lecture notes and learning resources optimized for use by the AI system. **Learning** : In MOOCs (Reich and Ruipérez-Valiente, 2019), a single set of course materials is designed to serve thousands of students with diverse backgrounds, and the pace of instruction is predetermined by the instructor, offering very limited room for personalized adaptation based on individual student needs (Yu et al., 2021). While in MAIC, course delivery is autonomously managed by AI teacher agents, which dynamically adjust the teaching process based on student interactions and inquiries. Additionally, MAIC offers AI teaching assistants and customizable AI classmates. Students can select the AI agents they wish to study with, thereby creating varied classroom scenarios that provide personalized learning companions, emotional support, and opportunities for knowledge discussion. 

In this report, we introduce the MAIC platform, offering an intuitive and user-friendly solution that accommodates the needs of various users, including students and educators. This platform comes pre-equipped with a suite of intelligent agents and tools that support course analysis and the construction of new MAIC course examples. Additionally, MAIC integrates several learning analytics tools powered by large models, enabling quick access to learning data, forecasting academic outcomes, and automating tasks such as interviews and assessments. 

With the support of Tsinghua University, one of China’s top universities, we conducted an exploration of this new learning model over a period of more than three months. Assisted by over 500 student volunteers, we implemented the study using two courses: the AI course “Towards Artificial General Intelligence” (TAGI) and the learning science course “How to Study in the University” (HSU). During this pilot, we collected over 100 _,_ 000 behavioral records. Based on the data from these courses, along with student survey measurements and qualitative interview results, we conducted an initial analysis of the features and performance of the MAIC system. In subsequent sections, we will briefly introduce the technical implementation, algorithm improvement and primary results of MAIC<sup>5</sup> . 

## **2 Related Work** 

**AI-assisted Online Learning** Online learning (Pappano, 2012) refers to the process of acquiring knowledge within an electronic environment composed of communication technologies, network infrastructure, artificial intelligence, and multimedia tools. While online education significantly enhances learners’ access to knowledge, supports personalized learning, and facilitates learning tailored to individual needs, persistent issues such as low course completion rates and suboptimal learning outcomes remain formidable challenges (Zhong et al., 2022). A retrospective study published by MIT (Reich and Ruipérez-Valiente, 2019) highlights that the lack of continuous guidance and personalized support for online learners is a critical factor affecting the quality of learning and student development in online settings. The inherent nature of online and remote learning often results in physical separation between students and instructors, making it prohibitively expensive to maintain real-time interactions through manual means (Aleven et al., 2015). Therefore, AI researchers have begun to introduce auxiliary learning applications such as resource recommendation systems (Jing and Tang, 2017) and intelligent teaching assistants (Jiang et al., 2019a; Tu et al., 2023) into online education environments. Leveraging technologies like educational knowledge graphs (Dang et al., 

> 5Our open-source Demo and detailed analysis will be released soon. More technical details are introduced in the companion papers Slide2Lecture and SimClass (Zhang et al., 2024). 

3 

2019; Yu et al., 2020), they are increasingly integrating diverse technologies to construct personalized online learning systems that enhance the learning experience through tailored support and adaptive learning pathways. In the era of large language models, platforms like Khan Academy have pioneered the deployment of AI-driven tools, such as the Khanmigo virtual tutor<sup>6</sup> . This development has sparked discussions among researchers about the potential to move beyond basic question-answering and recommendation functionalities, exploring the design of more deeply integrated models that fuse AI with online education in innovative ways (Golchin et al., 2024). Some of the research efforts gradually aim to create new paradigms that go beyond traditional approaches to AI-enhanced learning. 

**LLM-driven AI Tutoring System** The evolution of intelligent tutoring systems (ITS) from early expert systems to agent-based models in the era of large language models has undergone several transformations in interaction paradigms (Pal Chowdhury et al., 2024). During the 1980s and 1990s, ITS began leveraging expert systems and related technologies to deliver instruction aligned with learners’ cognitive processes across diverse educational settings. Representative systems from this period include AutoTutor, developed by the University of Memphis (Nye et al., 2014), and SCOT from Stanford University[51]. These systems offered greater flexibility and were among the first to support natural language-based question-and-answer interactions. However, the content of these interactions remained pre-designed, limiting their ability to provide learning support beyond the scope of the system’s initial design. The advent of Large Language Models (LLMs) has significantly broadened the scope of intelligent tutoring systems (ITS), offering unprecedented interactivity and adaptability across educational platforms (Bubeck et al., 2023). Recent strides in the study of multi-agent systems and the integration of tools have catalyzed new approaches to planning and student interaction within ITS frameworks (Park et al., 2023b; Qian et al., 2023; Schick et al., 2024). Emerging research (Chen et al., 2024) illustrates the capacity of LLMs to autonomously curate and deliver educational content by leveraging an array of tools. Additionally, innovations like MWPTutor (Pal Chowdhury et al., 2024) explore how LLMs can effectively manage the teaching of complex subjects, such as mathematical word problems, demonstrating their versatility in specialized learning environments. Building on these developments, our research focuses on an LLM-based ITS model designed to establish a robust framework for comprehensive, lecture-level tutoring that aligns with evolving educational standards, thereby reinforcing the transformative role of LLMs in the future of education. 

## **3 MAIC** 

In this section, we introduce the key techniques for implementing a MAIC platform. Specifically, we present the main workflows designed for both the teaching and learning sides, highlighting the key challenges associated with each and the corresponding solutions implemented to address these issues. 

### **3.1 Teaching: Course Preparation Workflow** 

To transform vast amounts of weakly structured and static learning resources (Dang et al., 2019) into highly structured and adaptive learning materials (Yu et al., 2021), MAIC develop a standardized course preparation workflow. This workflow is designed to streamline the workload of experts, facilitating the scalability of this online learning model and preparing it for broader implementation. Such course preparation workflow of MAIC consists of two major stage: **Read** and **Plan** . 

### **3.1.1 Read Stage** 

At this stage, instructors (and authorized teaching assistants) are involved by providing material. With the assistance of multi-agent systems empowered by large language models, they upload a set of course slides _P_ = _{Pi}_<sup>1</sup><sup>_≤i≤|P|_</sup> , which are then transformed into highly structured intelligent learning resources _P_<sup>�</sup> = _{⟨Pi, Di, Kj⟩}_<sup>1</sup> 1<sup>_≤_</sup> _≤_<sup>_i_</sup> _j_<sup>_≤|P|_</sup> _≤|P|_<sup>along with multiple AI agents designed for classroom</sup> construction. The _Pi_ and _Di_ here correspond to a single slide page and its textual description, while _Kj_ denotes to the knowledge-aware section of each page. 

> **1. Slides Content Extraction** . First, MAIC employs a multi-modal LLM (mLLM) (Huang et al., 2023) to capture the textual content _Pi_<sup>_t_and the visual content</sup><sup>_P v_</sup> _i_<sup>of each page of the given slide</sup><sup>_P_,</sup> 

> 6 `https://blog.khanacademy.org/teacher-khanmigo/` 

4 



<!-- Start of picture text -->
Slides Content Extraction Function Generation<br>ContentTextual P1 P2 P3 P4 ... Pn ShowFile Display the next slide.<br>before each slide page  P<br>Slides ContentVisual P1 P2 P3 P4 ... Pn ReadScript<br>Teach based on the current script.<br>inside each slide page  P<br>Structure Extraction<br>AskQuestion<br>Display the next slide.<br>P1P1P1 P1P1P1 Chapter 1: Multi-agent systems after each section  S<br> Section 1: Intro ... ...<br>D1 P1 P1<br>LLM D2 P2 P2 Agent Generation<br>... ... ... Teacher Assistant Manager<br> Section 2: Recent Works Teach & Answer Maintain Order & Control the Class<br>D1D1D1 Dn Pn Pn Questions Assist<br>Classmate(s) Analyzer Other Agents<br>Description Tree Structure Initiate Ideas & Analyze Learning ? Customized by<br>Generation Generation Discussions Performance users!<br>Read Stage Plan Stage<br><!-- End of picture text -->

Figure 2: An illustration of the course preparation workflow of MAIC. 

i.e., _fT_<sup>1:</sup><sup>_Pi→<P_</sup> _i_<sup>_t, P_</sup> _i_<sup>_v>_.Such functional model</sup><sup>_f_</sup> _T_<sup>1</sup> 7 can be adjusted and further improved by the arising LLM techniques, and the current implementation is based on the GPT-4V<sup>8</sup> model with certain prompting contexts. 

**2. Structure Extraction** . After the pre-processing of the uploaded slides, MAIC employs two functions to complete the read stage. The produced _< Pi_<sup>_t, P_</sup> _i_<sup>_v>_are described by an mLLM-based</sup> method with straightforward and comprehensive texts, i.e., _fT_<sup>2:</sup><sup>_<P_</sup> _i_<sup>_t, P_</sup> _i_<sup>_v>→Di_.Meanwhile,</sup> MAIC takes an knowledge extraction method to organize the core knowledge of each page and build a tree-style taxonomy for the slide, i.e., _fT_<sup>3:</sup><sup>_< P_</sup> _i_<sup>_t, P_</sup> _i_<sup>_v, Di>→Kj_, which makes up the final</sup><sup>_P_�.</sup> 

### **3.1.2 Plan Stage** 

At this stage, instructors (and authorized teaching assistants) are involved by proofreading and refining the results. Based on highly structured slides, MAIC constructs a novel instructional action representation language, allowing the incorporation of flexible teaching functions such as lecturing and questioning into preset classrooms, which naturally connects with related educational technologies like lecture script generation (Hong et al., 2023b) and question generation (Kurdi et al., 2020). Meanwhile, leveraging intelligent agent construction techniques (Chen et al., 2023), the platform utilizes course content to provide teachers and teaching assistants with AI-driven agents, facilitating the early planning of the foundational structure for subsequent courses. 

**3. Function Generation.** To make the heterogeneous teaching actions be generated within the classroom context, teaching activities such as lecturing and giving quizzes are conceptualized as _teaching actions_ within MAIC. Each teaching action _T_ is defined as _T_ = ( _type, value_ ), where _type_ indicates the category of the action (e.g., _ShowFile_ , _ReadScript_ , _AskQuestion_ ), and _value_ details the content of the action, such as the script to be read aloud. This approach reflects our principles of flexibility and adaptability, allowing classroom actions to be easily configurable. It empowers developers and educators to create custom teaching actions tailored to specific needs, facilitating their smooth integration into the overall teaching process. 

Each Function is associated with the generation of certain content, denoted as _< Tn, P_<sup>�</sup> _T >_ . For instance, the function _AskQuestion_ necessitates linkage with one or a set of specific questions. Among these, the most crucial action is _ReadScript_ , as it constitutes the core of the instructional process. Based on this function, these Teaching Actions are embedded within the course script 

> 7The same applies to similar symbols in the following text. 

> 8 `https://openai.com/index/gpt-4v-system-card/` 

5 



<!-- Start of picture text -->
 Current Slide Dialogue History<br>From Single-Agent to Multi-Agent<br>Multi-Agent System Now let's talk about LLM empowered  multi-agent<br>- What are multi-agent systems? systems. At the right side of the slide, we can see their<br>- How to Applicationsunderstand these systems? Teacher exciting applications in different fields. What's more, ...<br>- Social Simulation<br>- Software Development<br>- ... I can't wait for the incredible future with these systems!<br>P 36 / 58 I heard that some  behaviors emerge  in these agents!<br>Classmate<br>Who speaksnext? ... Wow, that sounds really interesting! As our classmate<br>said, are there any patterns  similar  to human groups?<br>Manager User<br>Class Roles<br>Good question! ...<br>Assistant<br>Interact with the class here ...<br>Teacher Assistant Classmate(s) User<br>Course Management Interactions in MAIC<br><!-- End of picture text -->

Figure 3: An illustration of the classroom learning environment of MAIC. 

using special marker symbols, thereby enabling the intelligent agent to read and invoke them in a personalized manner. Specifically, MAIC has trained a high-quality lecture script generation model based on long-context encoding methods and multi-modal model foundations, thereby supporting the fundamental class procedures as well as the integration of other teaching actions, i.e., _fT_<sup>4:</sup><sup>_P_�</sup><sup>_→_</sup> _P_ � _script_ . Then, MAIC provide a series of optional functions such as _fT_<sup>5:</sup><sup>_P_�</sup><sup>_→P_�</sup><sup>_question_for serving</sup> proactive questioning during the class. Note that all the generated results are required to be checked and adjusted by instructors, which guarantees the quality and correctness of the produced course. 

**4. Agent Generation.** Meanwhile, instructors can provide personalized information (such as the voice, teaching styles, and extended course material) for building customized teaching agents, such as Teacher Agent _aT_ and Teaching Assistant Agent _aT A_ . MAIC provides several agentization toolkits (Chen et al., 2023) that implemented via LLMs, supporting the high-level DIY of these agents. The extended course materials uploaded are also segmented in this section and integrated into different intelligent agents using the RAG (Retrieval-Augmented Generation) technology. The associated series of technological innovations are also thoroughly introduced and evaluated in the concurrent academic papers. 

### **3.2 Learning: Multi-agent Classroom Environment** 

As described in the Introduction, student learning in MAIC follows a _"1 Student user + N AI Agents"_ model. In such an environment, the AI teacher controls the learning progress based on the highly structured instructional action representation language mentioned earlier, explains course content, poses questions, and navigates PowerPoint slides, while the AI teaching assistant maintains classroom order and prevents content deviation. Students can interrupt the teacher at any time, ask questions, and engage in discussions, and the intelligent agents continuously adjust the teaching process and some content based on the students’ performance. As introduce in Zhang et al. (2024), the design principles for constructing this immersive adaptive classroom originate from the following two concerns: (1) How to ensure that the classroom covers the core classroom behaviors? (2) How to maintain the entirety of the interaction within the natural flow of the classroom process? 

In addressing the initial concern, we systematically classify classroom interaction behaviors in accordance with established educational principles, as delineated in Schwanke’s seminal work (Schwanke, 1981): _Teaching and Initiation (TI)_ encompasses the instructive actions of the teacher and the responsive feedback or insights provided by students; _In-depth Discussion (ID)_ involves the alignment, deliberation, and iterative question-and-answer exchanges between the teacher and students, which are instrumental in facilitating students’ conceptual comprehension; _Emotional Companionship (EC)_ pertains to the encouragement of student learning, the cultivation of a conducive learning environment, and the provision of emotional sustenance; and _Classroom Management (CM)_ refers to the 

6 

maintenance of order, the organization of disruptive elements, and the steering of classroom discourse. Recognizing that these pedagogical behaviors manifest through diverse **Class Roles** (represented as _R_<sup>�</sup> = _{ri}_<sup>_|_</sup> _R_<sup>�</sup> _|_ , with each _ri_ signifying a distinct role), it is imperative to ensure the _variety_ and _breadth_ of the agents’ roles within the educational setting. 

Addressing the subsequent concern, we emphasize the necessity of meticulously and rhythmically orchestrating the interactions among the various agents within the system, in harmony with the course content. With the Learning Materials (denoted as _C_ = [ _c_ 1 _, ..., ct_ ], where each instructional script _ct_ is sequenced), we introduce an innovative **Session Controller** designed to regulate the flow of classroom interactions, contingent upon the class’s dynamic state and under the aegis of a central managerial agent (Wu et al., 2023). 

Based on these principles, we construct multiple classmate agents for diverse roles, implement class control, and ultimately derive the multi-agent classroom process. 

**Classmate Agents.** To enhance the educational experience and emulate the dynamics of traditional classroom settings, we currently preset a variety of student-like agents, each imbued with unique personality traits, to complement the teaching agents. These agents are designed to perform roles akin to peer students, enriching the interactive landscape of the learning environment. In this scholarly work, we have introduced an initial set of four archetypal student agents, while also providing users with the flexibility to customize and introduce additional engaging student agents onto the educational platform. Each agent **a** _i ∈A_ is facilitated through prompting LLMs and associated with one or more class roles, denoted as: _A_ = _ρ_ ( _LLM,_ P _A_ ) _, A ⇔ R_<sup>�</sup> , where _ρ_ is the role customization operation, P _A_ is the system prompt with agent description (Zhang et al., 2024). 

_• Class Clown (TI, EC, CM)_ : Crafted to spark creativity, engender a lively classroom ambiance, and act as a supportive peer, this agent also assists the teacher in steering the class’s focus when the learner’s attention wanders. 

_• Deep Thinker (TI, ID)_ : This agent is dedicated to profound contemplation and to posing thoughtprovoking questions that challenge and extend the intellectual boundaries of the classroom. 

_• Note Taker (TI, CM)_ : With a penchant for summarizing and disseminating key points from the class discussions, this agent aids in the cognitive organization and retention of information for all participants. 

_• Inquisitive Mind (TI, EC)_ : Characterized by a propensity for inquiring about lecture content, this agent fosters a culture of inquiry and dialogue, prompting others to engage in critical thinking and collaborative discourse. 

Unlike Standardized Operating Procedures (SOPs) commonly used in multi-agent systems (Qian et al., 2023; Hong et al., 2023a), classroom scenarios function as dynamic, interactive environments without rigid workflows, resembling an evolving group discussion. In these settings, agents must determine appropriate timing for their interactions, adapting to the fluid nature of classroom discourse. To address this need, we designed a controller that observes classroom dynamics, makes informed decisions, and manages agents’ behaviors based on the current state of the class. The Session Controller is composed of three core modules: the Class State Receptor and Manager Agent. 

**Class State Receptor.** The Class State Receptor captures the ongoing classroom dialogue, with the history up to time _t_ represented as _Ht_ =<sup>�</sup> ( _u_<sup>**a**</sup> _i_<sup>_j_)</sup><sup>_t_,where</sup><sup>_ui_istheutterancemadebyagent</sup> **a** _j_ or a user (denoted as **a** _u_ ). The class state _St_ integrates this interaction data, structured as _St_ = � _Pt, Ht|R_<sup>�</sup> �. Here, _Pt ⊆ P_ represents the learning materials covered up to time _t_ . This design prioritizes adaptability and real-time decision-making, aligning with pedagogical principles that emphasize responsiveness to the evolving needs of learners within an educational setting. 

**Manager Agent.** Drawing inspiration from AutoGen (Wu et al., 2023) and MathVC (Yue et al., 2024), we designed a hidden meta-agent responsible for regulating the dynamics of classroom interactions. This agent receives the current class state _St_ , monitors the flow of the class, interprets ongoing activities, and determines the subsequent action to be executed, ensuring that the learning environment remains adaptive and responsive. The task _fL_ of the Manager Agent can be formally defined as _fL_ : _St →_ ( **a** _t, T_ ) _|_ **a** _t ∈A, Tn ⇐T_ . 

7 

where _Tn_ denotes a specific function, and the selected action will be carried out, transitioning the class to the next state. After executing an action, the system enters a waiting phase for a time window _τ_ . During this period, if a user responds or the waiting time elapses, the Manager Agent is triggered to make a new decision. This design reflects key educational principles by prioritizing a learnercentered approach, maintaining fluid class engagement, and promoting timely and contextually relevant instructional adjustments, thereby enhancing the overall educational experience. 

This classroom management method is the core of MAIC learning stage. Currently, we collect plenty interaction data and employ several foundation models (Hu et al., 2024; GLM et al., 2024) via fine-tuning or prompt tuning as our baseline model. 

## **4 Key Technique Evaluation** 

MAIC is a complex large language model-based intelligent agent system that encompasses various specific technologies. On the teaching side, it involves multiple processes for content generation and knowledge understanding, while on the learning side, it requires evaluating the effectiveness of agent construction and classroom management capabilities. Currently, we focus on presenting two core functions: lecture script generation and course management, which are fundamental to the teaching and learning aspects of MAIC. The evaluation of other technologies will be continuously updated. It is important to note that these assessments provide only an initial view of specific aspects of MAIC rather than its overall effectiveness, which will be further explored through real-world practice and results analysis in subsequent sections. 

### **4.1 Teaching Side Evaluation** 

**Function Generation** . As introduced in Section 3.1, generating vivid slide scripts is the core function of MAIC teaching workflow. **Baselines** : To assess the effectiveness of our implementation, we established two baseline configurations for comparison: (1) We replicated **_S_** _cript_ **_2T_** _ranscript_ (Nguyen et al., 2023), referred to as _S2T_ , which uses slide titles to offer overarching context and guidance for generating transcripts. (2) We also reproduced **_S_** _elf-_ **_C_** _ritique_ **_P_** _rompting_ (Zheng et al., 2024), denoted as _SCP_ , which incorporates a self-critique and refinement process to enhance script quality. 

**Evaluation Metrics** : Our evaluation employs four distinct metrics to rate the generated scripts on a 5-point Likert scale, where 1 represents unacceptable quality and 5 denotes optimal performance: 

1. _Tone_ evaluates whether the script appropriately reflects the instructional tone of a teacher. 

2. _Clarity_ measures how clear and comprehensible the script is for learners. 

3. _Supportiveness_ assesses the extent to which the script provides emotional and motivational support to students. 

4. _Alignment_ evaluates the degree to which the script content aligns with the slide material. 

Overall performance is determined by averaging the scores across all metrics. 

**Procedure** : We executed the course preparation pipeline for each baseline and collected script evaluations from annotators. To minimize potential bias, each slide was assessed by three independent annotators, who were required to provide ratings for all configurations of the same slide. This approach ensures a balanced and comprehensive evaluation of the teaching material, aligning with educational principles that emphasize clarity, support, and contextual relevance in instructional content. 

Table 1: Evaluation result of our implementation of generation. 

|**Setting**|**Tone**|**Clarity**|**Supportive**|**Matching**|**Overall**|
|---|---|---|---|---|---|
|S2T (Nguyen et al., 2023)|3.88|3.93|3.23|3.63|3.67|
|SCP (Zheng et al., 2024)|**4.03**|4.24|3.38|3.93|3.90|
|MAIC-FuncGen|4.00|**4.25**|**3.57**|**4.18**|**4.00**|
|w/o visual|3.78|3.73|3.44|3.51|3.61|
|w/o context|3.97|4.00|3.38|4.03|3.84|
|Human|4.02|4.07|3.38|3.98|3.86|



8 

**Results** : As shown in Table 1, our approach (MAIC-FuncGen) achieves the highest overall score of 4 _._ 00, outperforming all baseline methods. Our analysis reveals several key insights: 

- **Importance of Visual Input** : The inclusion of visual elements significantly enhances script generation quality. Both _S2T_ and MAIC-FuncGen without visual inputs received lower matching scores, highlighting the need for contextual visual cues that align the script content closely with the presented materials. 

- **Role of Contextual Information** : The presence of coherent contextual information, including content from previous pages, is critical for script quality. It not only improves the clarity of the current content but also enhances the supportive and matching aspects by providing a continuous and interconnected learning narrative. This aligns with pedagogical principles that emphasize coherence and context in learning materials to support deeper understanding. 

- **Comparative Performance with Human Instructors** : Interestingly, our approach slightly outperformed the human baseline across three key dimensions. This can be attributed to the inherent ability of large language models (LLMs) to strictly adhere to instructions, maintaining alignment with slide content and employing an encouraging and supportive tone. In contrast, human instructors often expand on topics freely, introducing their own style and diverging from the core content, which reflects a more flexible, albeit less structured, instructional approach. 

These findings underscore the value of integrating structured visual and contextual information into script generation, while also highlighting the potential of LLMs to complement traditional instructional strategies by providing consistency and structured support. 

### **4.2 Learning Side Evaluation** 

**Classroom Manager Agent** . Section 3.1.2 also mention several relevant t <mark>echniques of MAIC</mark> learning. The classroom <mark>manager agent is the</mark> keypoint of the classroom <mark>controlling.</mark> **<mark>Setup:</mark>** However, the evaluation of this process is highly subjective, making it chall <mark>enging to establish an</mark> objective scoring system for assessment. Therefore, in the practical implementation of the TAGI and HSU courses, we select 500 actual system decisions and extracted their corresponding classroom scenarios. We recruit expert teach- 



<!-- Start of picture text -->
Manager Agent<br>w/o description<br>40 50 60 70 80 90<br>Precision<br>TAGI<br>HSU<br>Overall<br><!-- End of picture text -->

Figure 4: Manager Agent Precision. 

ers and teaching assistants to manually annotate these scenarios. Based on this annotated data, we derive the results shown in Figure 4. These results illustrate the alignment between the actions chosen by the manager agent and those selected by human instructors in determining the next course action. Specifically, we evaluate the implementation with and without role description, detecting the effects of these contextual information. 

**Result:** Statistical analysis reveals that omitting role descriptions for each agent reduces the classifier’s performance. Although the LLM can sometimes identify the correct agent by referencing partial behaviors from the chat history, the inclusion of comprehensive role descriptions markedly enhances performance. This suggests that while leveraging chat history as input for the scene controller can provide some benefits, it is insufficient for consistently generating accurate outputs. 

The current results, however, remain below optimal levels, indicating further opportunities to refine and enhance the user experience. Despite the suboptimal performance, interacting agents demonstrate the capacity to partially offset these shortcomings. This compensatory effect is due to the LLM’s ability to manage user queries beyond the predefined functions of each agent, as evidenced by our subsequent behavioral study, where user ratings did not significantly decline in the ablation setting. 

Nonetheless, enhancing the accuracy of the controller agent remains advantageous, as agents can more effectively manage tasks they are specifically designed for. For example, the teacher agent is tailored to adopt a softer, more instructive tone, but it may be less effective in handling safety-related cases compared to the teaching assistant agent. Improved accuracy ensures that each agent operates within its designed scope, contributing to a more seamless and effective instructional process. 

9 

## **5 Behavioral Experiment** 

Following approval from Tsinghua University Science and Technology Ethics Committee (Certificate No: THU-04-2024-56) and the recruitment of student and teacher volunteers, we conduct over three months of teaching practice and behavioral analysis in the courses "Towards General Artificial Intelligence" and "How to Study in the University." This large-scale study involves more than 500 students and aims to address three core questions: **Q1:** What is the quality of MAIC Courses? **Q2:** What are the learning outcomes within MAIC? **Q3:** How do students perform in the MAIC environment? In the following sections, we present some preliminary observations from this study. 

### **5.1 Q1: The Quality of MAIC Course** 

We evaluated the quality of the MAIC course using the results from two questionnaires completed by course takers. The first questionnaire focused on the quality of AI teacher’s teaching, adapted from the Community of Inquiry Framework (Garrison and Arbaugh, 2007). Items in the original COI questionnaire were revised to make them suitable for the AI-engaged learning environment. This questionnaire was administered when students completed the whole course. 

As presented in Figure 5, the results showed that overall students had positive beliefs of the teaching quality on MAIC. For instance, the mean score of students’ rating on the question "The AI instructor clearly communicated important course goals" (Course Objective) was 4.12 (SD = 0 _._ 66) out of 5, and the average rating on "The AI instructor encouraged course participants to explore new concepts" was 4 _._ 03 (SD = 0 _._ 73). These findings suggest that students felt the AI instructors effectively helped them understand course objectives, clarify their thinking, explore new ideas, and engage in meaningful dialogue. 

|Timely Feedback<br>3.7|
|---|
|Understand Students<br>3.51|
|Discuss Problems<br>3.91|
|Encourage Exploration<br>4.03|
|Participate in Tasks<br>3.85|
|Get Involved<br>3.79|
|Clarify Thoughts<br>3.95|
|Understand Theme<br>3.77|
|Clear Instruction<br>3.77|
|Course Objectives<br>4.12|
|0.0<br>0.5<br>1.0<br>1.5<br>2.0<br>2.5<br>3.0<br>3.5<br>4.0<br>Evaluation Score|



Figure 5: Results from after-course survey. 

However, relatively lower ratings were observed on questions like “The AI instructor provided feedback that helped me understand my strengths and weaknesses” (Understand Student), which had a mean score of 3 _._ 51 (SD = 0 _._ 94). This indicates that AI instructors may lack personalization and adaptability during the teaching process, possibly because the same scripts were used for all students. 

### **5.2 Q2: The Behavior of MAIC Student Engagement** 

Firstly, when it comes to choosing the class mode, students tend to prefer the "continuous mode," believing that this mode allows them to maintain their train of thought without interruption, thereby ensuring learning efficiency. The "continuous mode" refers to a setting where, after selecting the teacher and other intelligent agent roles (such as teaching assistant, thinker, note-taker), the chosen roles conduct the class from start to finish without any interactive input from the students, making it a relatively passive learning approach. For example, during interviews, one student mentioned: 

> "I mostly used the continuous mode because, in the interactive mode, after the AI teacher finishes each sentence, you have to respond before they can continue. I don’t always feel like interacting after every sentence, so most of the time, I use continuous mode. Of course, there were one or two times when I used interactive mode because the AI prompted me to speak, but I remember that once, after I spoke in interactive mode, the AI didn’t respond or react to what I said, so I felt like it wasn’t very useful. After that, I just stuck with the continuous mode." In this mode, although interaction is not possible, some students adopt a pause strategy if they don’t understand something. For instance, one student mentioned, "If I didn’t understand something, I would pause and look at the PPT and the text in the text box. I don’t think I ever stopped to ask the AI to explain something again, unless it was some unfamiliar term or a more exploratory topic." 

10 

Secondly, regarding specific behaviors during the class, some students proactively ask questions to the intelligent agent around certain topics. As shown in Figure 3, 61% of the students’ behavior in class involved actively seeking knowledge, information, or asking questions. For example, asking "Can you explain the transformer structure in simple terms?" The interview results of this study also support this view. Many students indicated that they would actively ask questions. Some examples from the interviews include: 

- "When I asked a question, the AI would ask a follow-up question related to mine, and 

- I felt it was an amazing experience, like it was really guiding me to think more deeply. I think the questions it asked made a lot of sense. In that interactive mode, it could extend into many other discussions beyond the course content." 

- "I think this might be an advantage of AI teaching. Because, in a traditional classroom, 

- whether it’s a large class or even a small one, students nowadays are generally reluctant to ask questions. There are various reasons for this. Also, I think immediate Q&A helps me learn the material better. If I have a question, I can get an answer right away, and I think that immediate feedback is really valuable." 

Additionally, some students manage and control different intelligent agent roles and the class progress. These management-related behaviors account for 11% (Figure 6). For example, "Please go back to the previous slide," or "Please explain that in simpler terms," demonstrating strong autonomy and self-regulated learning abilities. In the interviews, some students also mentioned, _I don’t just ask for knowledge; I might ask, ’I want to learn more,’ or ’I hope to explore something new in a certain field,’ to manage and regulate the AI’s responses._ 

Overall, the findings reveal that while students prefer the "continuous mode" for its uninterrupted flow of information, this passive ap1.5% 18.1% proach may limit opportunities for active en0.7% Student Activity Type gagement and critical thinking. In the future, AI 9.6% Managing Progress agent-driven classes should actively encourage Managing Members student interaction rather than simply deliver5.3% Expressing Opinion ing continuous knowledge. In addition, the high 60.9% 3.9% Discussing or VerifyingAsking Questions level of proactive questioning indicates that stuOthers dents are eager to engage when given the opporAnswering or Responding tunity, underscoring the importance of designing AI tools that foster inquiry-based learning (Xie, Figure 6: Ratio of student activities. 2023). Questioning is an important behavior that reflects active learning in students, which ultimately leads to better academic performance. Finally, the occurrence of management-related behaviors suggests that students already realize their active role in their learning process, which align with Cain (2024)’ study. It is said that the capabilities of LLM AI tools can help students and educators transition from passive recipients to active co-creators of their learning experiences. Further research can give more support and encouragement for them to take an active role in directing their learning. 

### **5.3 Q3: The Outcome of MAIC Learning** 

We assessed the effectiveness of the MAIC course from three perspectives: performance in module tests and the final exam, technology acceptance through questionnaires, and self-reported higher-order thinking scores. 

**Test Results.** Module tests were conducted at the end of each module, focusing primarily on the content covered in the most recent module. The final exam was administered one week after the course concluded, synthesizing questions from the earlier module tests. Average attendance of the module tests is 76 _._ 3% (SD=6%), while that of the final exam is 73 _._ 3%. Test scores (stantardized to percentage) ranged from 53 _._ 3% (Module 2, SD=18 _._ 9%) to 82 _._ 4% (Module 4, SD=16 _._ 3%), reflecting students’ learning outcomes. These outcomes were corroborated by student interviews. One participant expressed, “My most impressive gains, from the perspective of knowledge, all came from the post-class test. If there were no post-class test, I might not remember the knowledge at all, and it might just pass by like a passing cloud of smoke... When I took the test and then looked back at the courseware, it was the peak period for me to absorb knowledge, honestly speaking.” 

11 

Additionally, test scores are strongly associated with class engagement. Specifically, the frequency (measured by the logorithm of the number of messages per module) and length of in-class chat messages (measured by the logorithm of the number of characters per message and module) —a prominent feature of the MAIC system—were positively correlated with standardized test scores and fi- 

Table 2: Correlation of students’ message-aware behavior and test results. Values shown in the table are normalized. 

|w/o control|_µ_(_log_(MsgNum))|_µ_(_log_(MsgLen))|
|---|---|---|
|AvgQuiz|0.341***|0.202*|
|FinalExam|0.346***|0.333**|
|w/ control|_µ_(_log_(MsgNum))|_µ_(_log_(MsgLen))|
|AvgQuiz|0.206**|0.177**|
|FinalExam|0.174|0.235*|



nal exam performance, as presented in Table 2. A regression analysis of standardized test scores on in-class chat message metrics was performed, controlling for normalized scores from Module 1. As Table 2 shows, in-class chat engagement is found to significantly predict higher test scores. 

**Technology Acceptance.** We further evaluate the acceptance of generative AI tools, such as ChatGPT, before and after the course. The results demonstrated a significant overall increase in technology acceptance ( _N_ = 111, _t_ = 3 _._ 05, _p_ = 0 _._ 002). Further analysis of specific dimensions of acceptance revealed significant improvements in Habit ( _t_ = 2 _._ 81, _p_ = 0 _._ 005), Effort Expectancy ( _t_ = 3 _._ 98, _p <_ 0 _._ 001), and Facilitating Conditions ( _t_ = 3 _._ 22, _p_ = 0 _._ 002). These findings indicate that students grew increasingly accustomed to and supportive of the MAIC course format. Interview responses also reflected an enhanced understanding and acceptance of AI technologies. One student remarked: 

"I used to be quite resistant to AI, mainly because it was too complicated, but after this course, I found that it was not that complicated, and I became more accepting of it. I also learned some of its principles." 

**High-order Thinking** . We explore the perceived impact of using LLMs on students’ higher-order thinking skills through pre- and post-course questionnaires. Comparative analyses and t-test results showed significant increases in students’ perceptions of the positive effects of the course on their abstract thinking ( _t_ = 2 _._ 32, _p_ = 0 _._ 02) and critical thinking ( _t_ = 2 _._ 37, _p_ = 0 _._ 02). These findings suggest that students believe using large language models throughout the course enhanced their cognitive abilities in these areas.Interviews further illuminated these perceptions. One student stated: 

"I think it might make me more confident in asking these questions and think more," while another mentioned, "Unlike before, (I was always) hiding and waiting for the opportunity to ask again." 

However, the course’s impact on other higher-order thinking skills remained ambiguous. Several students noted a lack of deep thinking and discussion opportunities in the course. For instance, one student commented: 

"(In a real classroom) After class, I can ask the teacher to explain it to me again... At this time, the teacher will definitely give you different ideas or explanations, but in this class, you will have no more after class." Another student added, "this course is purely about content because the teacher’s teaching is quite mechanical. The course is rich in theoretical knowledge, but there is almost no life thinking, life enlightenment, or some enlightenment and thinking outside of artificial intelligence." 

Notably, there is a limitation came from the questionnaire itself. As we evaluated students’ perceptions on the impacts on high-order thinking abilities, it should be noted that the abilities are not estimated. Future study should include designed scales or tasks to estimate the effects of the course on the students’ high-order thinking abilities. 

To address this limitation, future research should incorporate well-designed scales or specific tasks that can objectively measure students’ higher-order thinking abilities. These might include assessments that evaluate critical thinking, problem-solving, and analytical reasoning skills directly. By doing so, researchers can gain a more comprehensive understanding of the course’s effectiveness in enhancing 

12 

these abilities. Moreover, the inclusion of such measures would allow for a more rigorous evaluation of the course’s impact, providing stronger evidence to support or challenge the findings based on student perceptions alone. 

## **6 Predicted Impact and Ethical Consideration** 

### **6.1 Predicted Impact** 

The implementation of MAIC in online education is expected to revolutionize the learning experience by enhancing both scalability and adaptability. By leveraging multi-agent systems, MAIC can dynamically adjust to the needs of individual learners, providing personalized learning paths that were previously unattainable in traditional MOOCs. This personalized approach not only improves learning outcomes but also provides access to high-quality education across diverse socio-economic backgrounds, as it reduces the dependency on human instructors for content delivery. 

Moreover, MAIC is anticipated to address some of the inherent challenges of traditional online education, such as the one-size-fits-all model and the lack of real-time adaptability (Rizvi et al., 2022). The integration of AI-driven agents as teachers, teaching assistants, and classmates creates a more interactive and responsive learning environment. This shift promises to increase engagement and motivation among students, potentially leading to higher completion rates and deeper understanding of the material. 

However, it is crucial to acknowledge that the introduction of such a transformative system could also have unintended consequences. There may be a widening gap between students who adapt well to AI-powered learning environments and those who struggle with this new mode of education. Additionally, the reliance on AI systems could lead to reduced opportunities for human instructors, potentially diminishing the role of educators in the learning process. These impacts need to be carefully monitored and addressed through ongoing evaluation and refinement of the MAIC system. 

### **6.2 Ethical Considerations** 

The deployment of MAIC in online education brings forth significant ethical considerations that must be carefully evaluated (Almarzouqi et al., 2024). One of the foremost concerns is learner privacy and data security. The system’s reliance on large-scale data collection and analysis to personalize learning experiences raises questions about how student data is stored, accessed, and used. To mitigate these concerns, stringent data protection measures have been implemented, including encryption and anonymization of student records. However, given the sensitivity of educational data, continuous efforts to enhance security protocols are essential. 

Issues of discrimination and bias also present ethical challenges. While MAIC aims to provide a personalized learning experience for all students, there is a risk that the algorithms driving these personalized experiences may inadvertently reinforce existing biases, particularly if the training data is not sufficiently diverse. To address this, the development team has incorporated fairness-focused auditing procedures into the algorithmic design process. Although these measures are designed to minimize bias, it is recognized that no system is entirely immune to these challenges, and ongoing monitoring is required to ensure equitable outcomes. 

The accuracy of information and content regulation within MAIC is another critical area of ethical concern. As the system automates the creation and dissemination of educational content, there is a risk that inaccuracies could be propagated at scale. To mitigate this, content generated by the AI is regularly reviewed by subject matter experts and teaching assistants. Nonetheless, given the vast scale of content production, it is acknowledged that some errors may still occur. Thus, the system includes mechanisms for students and educators to flag and correct inaccuracies, ensuring continuous improvement of the educational material. 

In terms of the ethics of education, MAIC raises questions about the role of teachers in a system that increasingly relies on AI-driven instruction. While the system enhances scalability and provides personalized learning experiences, it also diminishes the direct involvement of human educators. This shift may impact the development of teacher-student relationships, which are critical for fostering emotional and social growth in learners (Thornberg et al., 2022). To address this, MAIC includes human-in-the-loop design principles, ensuring that educators can intervene and guide the AI’s 

13 

decision-making processes when necessary. However, the balance between AI automation and human oversight remains a complex issue that requires ongoing consideration. 

Furthermore, the lack of peer interaction in a predominantly AI-driven educational environment could hinder the development of important social skills among students. To counter this, MAIC incorporates AI classmates designed to simulate peer interactions. While these agents provide a form of interaction, they cannot fully replicate the nuances of human-to-human communication. The system, therefore, encourages mixed-mode learning environments where students can engage with both AI and human peers, preserving the benefits of social learning. 

Finally, the issue of student personalization must be approached with caution. While MAIC’s ability to adapt to individual learning needs is a significant advantage, it also poses risks to fairness and equality. There is a potential for certain students to receive more tailored and effective instruction based on their data profiles, potentially exacerbating educational inequalities. To mitigate this, MAIC includes mechanisms to ensure that all students, regardless of their data profiles, have access to high-quality learning experiences. The system’s fairness algorithms are continuously refined to promote equitable educational outcomes for all learners. 

## **7 Conclusion** 

In this paper, we provide a concise overview of the development trajectory of online education and the technological opportunities arising in the era of large language models. Considering the principles of adaptivity and scalability, along with the sophisticated design of LLM-driven multi-agent systems, we explore how existing MOOC can be transformed into MAIC (Massive AI-empowered Courses) and discuss new paradigms of teaching and learning. We propose a comprehensive solution, analyze the key technical components, and implement each step of the process. Our approach was practically deployed in two courses at Tsinghua University, leading to a series of preliminary observations of student behavior. These initial findings suggest that highly personalized classrooms built with new AI-assisted learning technologies can achieve high quality, and student behavior demonstrates the effectiveness of the teaching process. Moving forward, this work will be continuously maintained and expanded, aiming to develop an open and shared platform for educational exploration, academic research, and technological innovation. We hope our work will call upon and serve educational theorists, technology developers, and innovators to engage in discussions about the new online environment in the era of large language models. 

## **Acknowledgement** 

### **7.1 Author Contribution** 

**System Implementation** . Jifan Yu, Zheyuan Zhang, and Daniel Zhang-li designed the overall framework of the system. Zheyuan Zhang refined the workflow representation method used for controlling agents, while Daniel Zhang-li was responsible for the development and engineering deployment of several algorithms, including resource processing and function generation. Shangqing Tu oversaw security reviews and the integration of RAG methods. Linlu Gong collected the evaluation data from students. Nan Zhang and Ruixin Ni were responsible for project management and coordination throughout the development phase of MAIC, playing a crucial role in ensuring the quality of the final system. 

**Theoretical Investigation** . Zhanxin Hao and Ruimiao Li were responsible for the theoretical investigation and analysis of the MAIC concept, while Yang Dang contributed to the early development of this idea. All supervising professors provided valuable insights and guidance in the conceptualization of MAIC. 

**Toolkit Completion** . Haoxuan Li, Yuanchun Wang, Hanming Li, Jiayin Lin, Jinchang Zhou, and Nianyi Lin contributed to the development of various MAIC tools, including the cognitive diagnosis module, automated interview module, and automatic analysis module. Haohua Wang and Lijun Deng played significant roles in data collection and processing. 

**Course Practice** . Yisi Zhan and Chaojun Xiao were instrumental in the first round of MAIC pilot courses, handling a wide range of practical tasks, including the recruitment of student volunteers, provision of course materials, content review, and post-class management. Xusheng Dai refined the 

14 

course practice process, while Xuan Yan was deeply involved in course support activities. Their efforts were critical to the successful execution of the two courses. 

**Pedagogical analysis** . Under the guidance of Yu Zhang, Zhanxin Hao was responsible for the preliminary pedagogical evaluation of the MAIC system. Ruimiao Li, under the supervision of Manli Li, conducted key field research. Jie Cao, Fei Qin, and Jianxiao Jiang played crucial roles in the analysis process, overseeing tasks such as automated coding, qualitative interviews, and data analysis, respectively. 

**Paper Writing** . Jifan Yu was responsible for the primary writing of the manuscript, while Zhanxin Hao and Ruimiao Li contributed significantly to the design and execution of the behavioral experiments and the ethical consideration. 

**Advising** . Manli Li, Juanzi Li, Zhiyuan Liu, Huiqin Liu, and Maosong Sun took advisor roles in this project. Xu Han brought technical insights into the system design. This project also received guidance and support from various relevant departments at Tsinghua University. 

### **7.2 Acknowledgement** 

This research project is supported by a grant from the Institute for Guo Qiang, Tsinghua University (20192920479). 

This project would like to express its appreciation for the contributions and assistance of many other participants. The artistic design was skillfully provided by Shanshan Wang. The platform development and feature implementation were carefully carried out by Peng Zhou, Yuting Liu, Yuanwei Xu and Chengqiang Xu. 

## **References** 

- Josh Achiam, Steven Adler, Sandhini Agarwal, Lama Ahmad, Ilge Akkaya, Florencia Leoni Aleman, Diogo Almeida, Janko Altenschmidt, Sam Altman, Shyamal Anadkat, et al. Gpt-4 technical report. _arXiv preprint arXiv:2303.08774_ , 2023. 

- Vincent Aleven, Jonathan Sewall, Octav Popescu, Franceska Xhakaj, Dhruv Chand, Ryan Baker, Yuan Wang, George Siemens, Carolyn Rosé, and Dragan Gasevic. The beginning of a beautiful friendship? intelligent tutoring systems and moocs. In _Artificial Intelligence in Education: 17th International Conference, AIED 2015, Madrid, Spain, June 22-26, 2015. Proceedings 17_ , pages 525–528. Springer, 2015. 

- Amina Almarzouqi, Ahmad Aburayya, Raghad Alfaisal, Mohamed Ahmad Elbadawi, and Said A Salloum. Ethical implications of using chatgpt in educational environments: A comprehensive review. _Artificial Intelligence in Education: The Power and Dangers of ChatGPT in the Classroom_ , pages 185–199, 2024. 

- Sébastien Bubeck, Varun Chandrasekaran, Ronen Eldan, Johannes Gehrke, Eric Horvitz, Ece Kamar, Peter Lee, Yin Tat Lee, Yuanzhi Li, Scott Lundberg, Harsha Nori, Hamid Palangi, Marco Tulio Ribeiro, and Yi Zhang. Sparks of artificial general intelligence: Early experiments with gpt-4, 2023. URL `https://arxiv.org/abs/2303.12712` . 

- William Cain. Prompting change: exploring prompt engineering in large language model ai and its potential to transform education. _TechTrends_ , 68(1):47–57, 2024. 

- Weize Chen, Yusheng Su, Jingwei Zuo, Cheng Yang, Chenfei Yuan, Chen Qian, Chi-Min Chan, Yujia Qin, Yaxi Lu, Ruobing Xie, et al. Agentverse: Facilitating multi-agent collaboration and exploring emergent behaviors in agents. _arXiv preprint arXiv:2308.10848_ , 2(4):6, 2023. 

- Yulin Chen, Ning Ding, Hai-Tao Zheng, Zhiyuan Liu, Maosong Sun, and Bowen Zhou. Empowering private tutoring by chaining large language models, 2024. URL `https://arxiv.org/abs/2309. 08112` . 

- D Cormier. The cck08 mooc – connectivism course, 1/4 way, 2008. URL `https://davecormier. com/edblog/2008/10/02/the-cck08-mooc-connectivism-course-14-way/` . 

15 

- Furong Dang, Jintao Tang, and Shasha Li. Mooc-kg: A mooc knowledge graph for cross-platform online learning resources. In _2019 IEEE 9th International Conference on Electronics Information and Emergency Communication (ICEIEC)_ , pages 1–8. IEEE, 2019. 

- John Daniel. Making sense of moocs: Musings in a maze of myth, paradox and possibility. _Journal of interactive Media in education_ , 2012(3):18–18, 2012. 

- Ziv Epstein, Aaron Hertzmann, Investigators of Human Creativity, Memo Akten, Hany Farid, Jessica Fjeld, Morgan R Frank, Matthew Groh, Laura Herman, Neil Leach, et al. Art and the science of generative ai. _Science_ , 380(6650):1110–1111, 2023. 

- Friedrich Froebel. _The education of man_ , volume 5. A. Lovell & Company, 1886. 

- D Randy Garrison and J Ben Arbaugh. Researching the community of inquiry framework: Review, issues, and future directions. _The Internet and higher education_ , 10(3):157–172, 2007. 

- Team GLM, Aohan Zeng, Bin Xu, Bowen Wang, Chenhui Zhang, Da Yin, Diego Rojas, Guanyu Feng, Hanlin Zhao, Hanyu Lai, et al. Chatglm: A family of large language models from glm-130b to glm-4 all tools. _arXiv preprint arXiv:2406.12793_ , 2024. 

- Shahriar Golchin, Nikhil Garuda, Christopher Impey, and Matthew Wenger. Large language models as moocs graders. _arXiv preprint arXiv:2402.03776_ , 2024. 

- Mark Halstead and Monica J Taylor. _Values in education and education in values_ . Routledge, 2005. 

- Sirui Hong, Xiawu Zheng, Jonathan Chen, Yuheng Cheng, Jinlin Wang, Ceyao Zhang, Zili Wang, Steven Ka Shing Yau, Zijuan Lin, Liyang Zhou, et al. Metagpt: Meta programming for multi-agent collaborative framework. _arXiv preprint arXiv:2308.00352_ , 2023a. 

- Xudong Hong, Asad Sayeed, Khushboo Mehra, Vera Demberg, and Bernt Schiele. Visual writing prompts: Character-grounded story generation with curated image sequences. _Transactions of the Association for Computational Linguistics_ , 11:565–581, 2023b. 

- Shengding Hu, Yuge Tu, Xu Han, Chaoqun He, Ganqu Cui, Xiang Long, Zhi Zheng, Yewei Fang, Yuxiang Huang, Weilin Zhao, et al. Minicpm: Unveiling the potential of small language models with scalable training strategies. _arXiv preprint arXiv:2404.06395_ , 2024. 

- Hanyao Huang, Ou Zheng, Dongdong Wang, Jiayi Yin, Zijin Wang, Shengxuan Ding, Heng Yin, Chuan Xu, Renjie Yang, Qian Zheng, et al. Chatgpt for shaping the future of dentistry: the potential of multi-modal large language model. _International Journal of Oral Science_ , 15(1):29, 2023. 

- Lan Jiang, Shuhan Hu, Mingyu Huang, Zhichun Wang, Jinjian Yang, Xiaoju Ye, and Wei Zheng. Massistant: a personal knowledge assistant for mooc learners. In _Proceedings of the 2019 Conference on Empirical Methods in Natural Language Processing and the 9th International Joint Conference on Natural Language Processing (EMNLP-IJCNLP): System Demonstrations_ , pages 133–138, 2019a. 

- Weijie Jiang, Zachary A Pardos, and Qiang Wei. Goal-based course recommendation. In _Proceedings of the 9th international conference on learning analytics & knowledge_ , pages 36–45, 2019b. 

- Xia Jing and Jie Tang. Guess you like: course recommendation in moocs. In _Proceedings of the international conference on web intelligence_ , pages 783–789, 2017. 

- Tumaini Kabudi, Ilias Pappas, and Dag Håkon Olsen. Ai-enabled adaptive learning systems: A systematic mapping of the literature. _Computers and Education: Artificial Intelligence_ , 2:100017, 2021. 

- Daphne Koller and Andrew Ng. The online revolution: Education for everyone. In _Seminar presentation at the Said Business School_ . Oxford University England, 2013. 

- Ghader Kurdi, Jared Leo, Bijan Parsia, Uli Sattler, and Salam Al-Emari. A systematic review of automatic question generation for educational purposes. _International Journal of Artificial Intelligence in Education_ , 30:121–204, 2020. 

16 

- Amir Hossein Nabizadeh, José Paulo Leal, Hamed N Rafsanjani, and Rajiv Ratn Shah. Learning path personalization and recommendation methods: A survey of the state-of-the-art. _Expert Systems with Applications_ , 159:113596, 2020. 

- Nguyen Xuan Vu Nguyen, Quang Huy Ngo, and Quang Nhat Minh Pham. Automatic transcript generation from presentation slides. In Chu-Ren Huang, Yasunari Harada, Jong-Bok Kim, Si Chen, Yu-Yin Hsu, Emmanuele Chersoni, Pranav A, Winnie Huiheng Zeng, Bo Peng, Yuxi Li, and Junlin Li, editors, _Proceedings of the 37th Pacific Asia Conference on Language, Information and Computation_ , pages 670–678, Hong Kong, China, December 2023. Association for Computational Linguistics. URL `https://aclanthology.org/2023.paclic-1.67` . 

- Benjamin D Nye, Arthur C Graesser, and Xiangen Hu. Autotutor and family: A review of 17 years of natural language tutoring. _International Journal of Artificial Intelligence in Education_ , 24: 427–469, 2014. 

- Sankalan Pal Chowdhury, Vilém Zouhar, and Mrinmaya Sachan. Autotutor meets large language models: A language model tutor with rich pedagogy and guardrails. In _Proceedings of the Eleventh ACM Conference on Learning @ Scale_ , L@S ’24, page 5–15, New York, NY, USA, 2024. Association for Computing Machinery. ISBN 9798400706332. doi: 10.1145/3657604.3662041. URL `https://doi.org/10.1145/3657604.3662041` . 

- Stamatios Papadakis. Moocs 2012-2022: An overview. _Advances in Mobile Learning Educational Research_ , 3(1):682–693, 2023. 

- Laura Pappano. The year of the mooc. _The New York Times_ , 2(12):2012, 2012. 

- Joon Sung Park, Joseph O’Brien, Carrie Jun Cai, Meredith Ringel Morris, Percy Liang, and Michael S Bernstein. Generative agents: Interactive simulacra of human behavior. In _Proceedings of the 36th annual acm symposium on user interface software and technology_ , pages 1–22, 2023a. 

- Joon Sung Park, Joseph C. O’Brien, Carrie J. Cai, Meredith Ringel Morris, Percy Liang, and Michael S. Bernstein. Generative agents: Interactive simulacra of human behavior. In _In the 36th Annual ACM Symposium on User Interface Software and Technology (UIST ’23)_ , UIST ’23, New York, NY, USA, 2023b. Association for Computing Machinery. 

- Chen Qian, Xin Cong, Cheng Yang, Weize Chen, Yusheng Su, Juyuan Xu, Zhiyuan Liu, and Maosong Sun. Communicative agents for software development. _arXiv preprint arXiv:2307.07924_ , 6, 2023. 

- Justin Reich. Rebooting mooc research. _Science_ , 347(6217):34–35, 2015. 

- Justin Reich and José A Ruipérez-Valiente. The mooc pivot. _Science_ , 363(6423):130–131, 2019. 

- Saman Rizvi, Bart Rienties, Jekaterina Rogaten, and René F Kizilcec. Beyond one-size-fits-all in moocs: Variation in learning design and persistence of learners in different cultural and socioeconomic contexts. _Computers in Human Behavior_ , 126:106973, 2022. 

- Timo Schick, Jane Dwivedi-Yu, Roberto Dessì, Roberta Raileanu, Maria Lomeli, Eric Hambro, Luke Zettlemoyer, Nicola Cancedda, and Thomas Scialom. Toolformer: Language models can teach themselves to use tools. _Advances in Neural Information Processing Systems_ , 36, 2024. 

- Dean Schwanke. Classroom interaction research: A survey of recent literature. _Journal of Classroom Interaction_ , pages 8–10, 1981. 

- Robert Thornberg, Camilla Forsberg, Eva Hammar Chiriac, and Ylva Bjereld. Teacher–student relationship quality and student engagement: A sequential explanatory mixed-methods study. _Research papers in education_ , 37(6):840–859, 2022. 

- Hugo Touvron, Thibaut Lavril, Gautier Izacard, Xavier Martinet, Marie-Anne Lachaux, Timothée Lacroix, Baptiste Rozière, Naman Goyal, Eric Hambro, Faisal Azhar, et al. Llama: Open and efficient foundation language models. _arXiv preprint arXiv:2302.13971_ , 2023. 

- Shangqing Tu, Zheyuan Zhang, Jifan Yu, Chunyang Li, Siyu Zhang, Zijun Yao, Lei Hou, and Juanzi Li. Littlemu: Deploying an online virtual teaching assistant via heterogeneous sources integration and chain of teach prompts. In _Proceedings of the 32nd ACM International Conference on Information and Knowledge Management_ , pages 4843–4849, 2023. 

17 

- Qingyun Wu, Gagan Bansal, Jieyu Zhang, Yiran Wu, Shaokun Zhang, Erkang Zhu, Beibin Li, Li Jiang, Xiaoyun Zhang, and Chi Wang. Autogen: Enabling next-gen llm applications via multi-agent conversation framework. _arXiv preprint arXiv:2308.08155_ , 2023. 

- Xiaofang Xie. Influence of ai-driven inquiry teaching on learning outcomes. _International Journal of Emerging Technologies in Learning_ , 18(23), 2023. 

- Ramazan Yilmaz, Halil Yurdugul, Fatma Gizem Karaoglan Yilmaz, Muhittin Sahin, Sema Sulak, Furkan Aydin, Mustafa Tepgec, Cennet Terzi Muftuoglu, and ORAL Omer. Smart mooc integrated with intelligent tutoring: A system architecture and framework model proposal. _Computers and Education: Artificial Intelligence_ , 3:100092, 2022. 

- Jifan Yu, Gan Luo, Tong Xiao, Qingyang Zhong, Yuquan Wang, Wenzheng Feng, Junyi Luo, Chenyu Wang, Lei Hou, Juanzi Li, et al. Mooccube: A large-scale data repository for nlp applications in moocs. In _Proceedings of the 58th annual meeting of the association for computational linguistics_ , pages 3135–3142, 2020. 

- Jifan Yu, Yuquan Wang, Qingyang Zhong, Gan Luo, Yiming Mao, Kai Sun, Wenzheng Feng, Wei Xu, Shulin Cao, Kaisheng Zeng, et al. Mooccubex: a large knowledge-centered repository for adaptive learning in moocs. In _Proceedings of the 30th ACM International Conference on Information & Knowledge Management_ , pages 4643–4652, 2021. 

- Murong Yue, Wijdane Mifdal, Yixuan Zhang, Jennifer Suh, and Ziyu Yao. Mathvc: An llm-simulated multi-character virtual classroom for mathematics education. _arXiv preprint arXiv:2404.06711_ , 2024. 

- Hao Zhang, Tao Huang, Zhihan Lv, SanYa Liu, and Zhili Zhou. Mcrs: A course recommendation system for moocs. _Multimedia Tools and Applications_ , 77:7051–7069, 2018. 

- Zheyuan Zhang, Daniel Zhang-Li, Jifan Yu, Linlu Gong, Jinchang Zhou, Zhiyuan Liu, Lei Hou, and Juanzi Li. Simulating classroom education with llm-empowered agents. _arXiv preprint arXiv:2406.19226_ , 2024. 

- Ying Zheng, Xueyi Li, Yaying Huang, Qianru Liang, Teng Guo, Mingliang Hou, Boyu Gao, Mi Tian, Zitao Liu, and Weiqi Luo. Automatic Lesson Plan Generation via Large Language Models with Selfcritique Prompting. In Andrew M. Olney, Irene-Angelica Chounta, Zitao Liu, Olga C. Santos, and Ig Ibert Bittencourt, editors, _Artificial Intelligence in Education. Posters and Late Breaking Results, Workshops and Tutorials, Industry and Innovation Tracks, Practitioners, Doctoral Consortium and Blue Sky_ , volume 2150, pages 163–178. Springer Nature Switzerland, Cham, 2024. ISBN 978-3-031-64314-9 978-3-031-64315-6. doi: 10.1007/978-3-031-64315-6_13. URL `https: //link.springer.com/10.1007/978-3-031-64315-6_13` . Series Title: Communications in Computer and Information Science. 

- Qingyang Zhong, Jifan Yu, Zheyuan Zhang, Yiming Mao, Yuquan Wang, Yankai Lin, Lei Hou, Juanzi Li, and Jie Tang. Towards a general pre-training framework for adaptive learning in moocs. _arXiv preprint arXiv:2208.04708_ , 2022. 

- Meina Zhu, Annisa R Sari, and Mimi Miyoung Lee. A comprehensive systematic review of mooc research: Research techniques, topics, and trends from 2009 to 2019. _Educational Technology Research and Development_ , 68:1685–1710, 2020. 

18 

