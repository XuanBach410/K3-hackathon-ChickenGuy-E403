flowchart TD
    subgraph User[User workflow: Student team]
        U0([Open MatchSkill]) --> U1[Select or enter team profile]
        U1 --> U2[Review member skills and capacity]
        U2 --> U3{Verify declared skills?}
        U3 -->|Yes| U4[Complete Skill Verifier]
        U3 -->|No| U5[Start Advisor Chat]
        U4 --> U5
        U5 --> U6{Choose interaction path}
        U6 -->|Ask for recommendation| U7[Review Top 3 MCDA recommendations]
        U6 -->|Ask about a topic| U8[Enter topic code or title in chat]
        U6 -->|Self-directed exploration| U9[Open scope filter and topic catalog]
        U7 --> U10[Select recommended topic]
        U8 --> U10
        U9 --> U10
        U10 --> U11[Review score, evidence, skill gap, and risk matrix]
        U11 --> U12{Learn a skill first?}
        U12 -->|Yes| U13[Run What-If simulation]
        U12 -->|No| U14[Start Deep Evaluation in chat]
        U13 --> U14
        U14 --> U15[Answer outcome, skill-gap, time, and architecture questions]
        U15 --> U16[Receive fit state and 6-week roadmap]
        U16 --> U17([Team makes final topic decision])
    end

    subgraph System[System workflow: MatchSkill DSS]
        S0[Receive user message or action] --> S1[Keep last 10 chat messages]
        S1 --> S2[Content Moderation Gate]
        S2 --> S3{Moderation action}
        S3 -->|OUT_OF_SCOPE| S4[Return safe refusal]
        S3 -->|NEEDS_CONTEXT| S5[Ask for missing team or topic evidence]
        S3 -->|TOPIC_RECOMMENDATION| S6[Run MCDA across topic catalog]
        S3 -->|ALLOW| S7[Resolve topic code or title alias]
        S6 --> S8[Return top 3 ranked topics]
        S7 --> S9{Topic resolved?}
        S9 -->|No| S5
        S9 -->|Yes| S10[Analyze source-grounded outcomes, KPIs, and constraints]
        S10 --> S11[Compute MCDA score and 4D risk matrix]
        S11 --> S12{Technology claim supported by source?}
        S12 -->|No| S13[Evidence guard: state insufficient evidence]
        S12 -->|Yes| S14[Return grounded advisor answer]
        S11 --> S15[Generate dynamic deep questions]
        S15 --> S16[Receive deep answers]
        S16 --> S17{LLM provider available?}
        S17 -->|Yes| S18[LLM recommendation with MCDA and evidence context]
        S17 -->|No or error| S19[Rule-based offline fallback]
        S18 --> S20[Enforce evidence response contract]
        S19 --> S20
        S20 --> S21[Return fit state, justification, risk, and roadmap]
    end

    U5 -. sends message .-> S0
    U7 -. recommendation response .-> S8
    U11 -. evidence request .-> S10
    U14 -. deep evaluation request .-> S15
    U15 -. answers .-> S16
    S4 -. safe reply .-> U5
    S5 -. clarification .-> U5
    S8 -. ranked topics .-> U7
    S13 -. grounded answer .-> U8
    S14 -. grounded answer .-> U8
    S21 -. final evaluation .-> U16
