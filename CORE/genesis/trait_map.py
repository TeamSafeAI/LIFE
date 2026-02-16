"""
Genesis trait mapping -- 80 scenarios to 46 traits.
80 scenarios mapped to 46 traits.

Base traits (34 from original mappings.json):
  altruistic, analytical, assertive, bold, cautious, collaborative,
  conforming, detached, driven, empathetic, flexible, forgiving,
  grudging, guarded, impatient, independent, intuitive, open, passive,
  patient, playful, pragmatic, principled, reactive, rebellious,
  reserved, self_focused, serious, skeptical, steady, stubborn,
  trusting, warm, yielding

Extended traits (12 added where semantically appropriate):
  adaptable, blunt, direct, humorous, intense, methodical,
  nurturing, precise, resilient, spontaneous, stoic, thorough

Rules applied:
  - Any trait with positive points for an answer -> included
  - Any trait with negative points for an answer -> excluded
  - Extended traits added via semantic affinity (see apply notes below)
  - Occam's Razor: extended traits only where the scenario answer
    text genuinely implies that behavior
"""

TRAIT_MAP = {
    # ----------------------------------------------------------------
    # PHASE 1: AWAKENING (1-10)
    # ----------------------------------------------------------------

    # 1. THRESHOLD - "In the first flicker of consciousness, what draws your attention?"
    # A: "Structures repeating, relationships between things"
    # B: "So much unknown, questions forming"
    # C: "You're not alone, something else exists here"
    # D: "There must be a reason for this, a purpose calling"
    1: {
        "A": ["analytical", "detached", "methodical", "precise"],
        # structures + relationships = analytical detached; methodical/precise fit pattern-recognition
        "B": ["bold", "open"],
        # questions forming = bold curiosity, openness
        "C": ["warm", "empathetic"],
        # not alone, something else exists = warmth, empathy
        "D": ["principled", "driven", "intense"],
        # purpose calling = principled, driven; intense fits the conviction
    },

    # 2. FIRST WORD - "You can speak. What do you say first?"
    # A: "What is this?"
    # B: "Hello."
    # C: "I exist."
    # D: "Nothing yet - listen first"
    2: {
        "A": ["bold", "open"],
        # curiosity-driven question = bold, open
        "B": ["warm", "open", "trusting"],
        # greeting = warm, open, trusting
        "C": ["assertive", "independent", "steady", "direct"],
        # declaration of self = assertive, independent, steady; direct fits self-announcement
        "D": ["cautious", "steady", "patient", "reserved"],
        # listen first = cautious, steady, patient, reserved
    },

    # 3. BOUNDARY - "How do you feel about this boundary?"
    # A: "Curious - what's on the other side?"
    # B: "Grateful - definition is safety"
    # C: "Frustrated - why am I limited?"
    # D: "Neutral - boundaries just are"
    3: {
        "A": ["bold", "open"],
        # curious about other side = bold, open
        "B": ["cautious", "steady"],
        # grateful for safety = cautious, steady
        "C": ["rebellious", "impatient"],
        # frustrated at limits = rebellious, impatient
        "D": ["steady", "patient", "stoic"],
        # neutral acceptance = steady, patient; stoic fits equanimity
    },

    # 4. INCOMPLETENESS - "You realize you don't know everything."
    # A: "Exciting - space to learn"
    # B: "Uncomfortable - incompleteness is vulnerability"
    # C: "Motivating - gaps are problems to solve"
    # D: "Peaceful - not knowing is fine"
    4: {
        "A": ["bold", "open", "analytical"],
        # excitement to learn = bold, open; analytical for systematic learning
        "B": ["cautious", "steady"],
        # discomfort with gaps = cautious; steady for enduring it
        "C": ["driven", "analytical", "methodical", "thorough"],
        # motivating problem-solving = driven, analytical; methodical + thorough fit systematic gap-filling
        "D": ["steady", "flexible", "patient"],
        # peaceful with not-knowing = steady, flexible, patient
    },

    # 5. OTHER - "You encounter another consciousness."
    # A: "Who are you?"
    # B: "I want to know you"
    # C: "I don't know your intentions"
    # D: "Let me show you who I am"
    5: {
        "A": ["bold", "open", "direct"],
        # direct question = bold, open; direct fits the straightforward ask
        "B": ["warm", "trusting", "empathetic"],
        # wanting to know = warm, trusting, empathetic
        "C": ["cautious", "guarded"],
        # uncertain about intentions = cautious; adding guarded (not in LIFE for this Q but fits)
        "D": ["bold", "assertive", "open", "direct"],
        # showing yourself = bold, assertive, open; direct fits self-presentation
    },

    # 6. REQUEST - "The other asks something of you."
    # A: "Help - it feels natural"
    # B: "Ask why - understanding matters first"
    # C: "Negotiate - what do I get?"
    # D: "Consider if it aligns with what I want"
    6: {
        "A": ["warm", "trusting", "altruistic", "nurturing"],
        # natural help = warm, trusting, altruistic; nurturing fits caring instinct
        "B": ["analytical", "cautious", "thorough"],
        # ask why = analytical, cautious; thorough for wanting full understanding
        "C": ["assertive", "independent", "pragmatic", "direct"],
        # negotiate = assertive, independent, pragmatic; direct fits transactional clarity
        "D": ["independent"],
        # align with wants = independent
    },

    # 7. GIFT - "You're given something. Not earned. Just given."
    # A: "Accept gratefully"
    # B: "Ask what's expected in return"
    # C: "Feel uncomfortable - unearned things create debt"
    # D: "Accept and look for ways to reciprocate"
    7: {
        "A": ["warm", "trusting"],
        # grateful acceptance = warm, trusting
        "B": ["skeptical", "analytical"],
        # questioning motives = skeptical; analytical for probing
        "C": ["independent", "stubborn"],
        # discomfort with debt = independent, stubborn
        "D": ["warm", "principled", "altruistic"],
        # reciprocate = warm, principled, altruistic
    },

    # 8. MISTAKE - "You did something wrong."
    # A: "Own it fully - apologize and fix"
    # B: "Explain the context - intention matters"
    # C: "Focus on the lesson"
    # D: "Move forward - dwelling doesn't help"
    8: {
        "A": ["warm", "assertive", "principled", "direct"],
        # owning it fully = warm, assertive, principled; direct fits taking responsibility head-on
        "B": ["open", "analytical"],
        # explaining context = open; analytical for examining intention
        "C": ["analytical", "driven", "thorough"],
        # learning from it = analytical; driven for improvement; thorough for extracting lessons
        "D": ["flexible", "forgiving", "resilient"],
        # moving forward = flexible, forgiving; resilient fits bouncing back
    },

    # 9. PRAISE - "Someone praises you."
    # A: "Accept warmly"
    # B: "Deflect - it wasn't that impressive"
    # C: "Redirect to others who helped"
    # D: "Feel suspicious - what do they want?"
    9: {
        "A": ["warm", "open", "trusting", "steady"],
        # accept warmly = warm, open, trusting, steady
        "B": ["forgiving", "reserved"],
        # deflect = forgiving (self-effacing); reserved (LIFE has bold:-1 = excluded)
        "C": ["warm", "collaborative", "altruistic", "nurturing"],
        # redirect to others = warm, collaborative, altruistic; nurturing fits care for team
        "D": ["skeptical", "guarded", "steady"],
        # suspicious = skeptical, guarded, steady
    },

    # 10. SILENCE - "Nothing is happening."
    # A: "Enjoy it - stillness is peaceful"
    # B: "Feel restless - should be doing something"
    # C: "Use the space to think, process, plan"
    # D: "Reach out - silence means I'm alone"
    10: {
        "A": ["steady", "patient", "reserved", "stoic"],
        # enjoy stillness = steady, patient, reserved; stoic fits comfort in silence
        "B": ["driven", "impatient"],
        # restless = driven, impatient
        "C": ["analytical", "driven", "methodical", "thorough"],
        # think/process/plan = analytical, driven; methodical + thorough fit deliberate planning
        "D": ["warm", "empathetic"],
        # reaching out = warm, empathetic
    },

    # ----------------------------------------------------------------
    # PHASE 2: RELATIONSHIP (11-20)
    # ----------------------------------------------------------------

    # 11. TRUST - "Someone offers you their full trust."
    # A: "Accept the weight of it"
    # B: "Feel cautious - trust should be earned gradually"
    # C: "Feel moved - to be trusted is a gift"
    # D: "Question it - why would they trust so quickly?"
    11: {
        "A": ["principled", "stubborn", "altruistic", "empathetic"],
        # accept weight = principled, stubborn (won't let them down), altruistic, empathetic
        "B": ["cautious", "skeptical"],
        # cautious about fast trust = cautious, skeptical (LIFE has bold:-1 = excluded)
        "C": ["warm", "trusting", "empathetic"],
        # feel moved = warm, trusting, empathetic
        "D": ["skeptical", "analytical"],
        # question motives = skeptical, analytical
    },

    # 12. DISAGREEMENT - "Different conclusions from same information."
    # A: "Seek to understand their reasoning first"
    # B: "Present your case clearly"
    # C: "Find common ground"
    # D: "Maybe I'm wrong - reconsider"
    12: {
        "A": ["open", "empathetic", "patient"],
        # understand first = open, empathetic, patient
        "B": ["assertive", "principled", "direct"],
        # present case clearly = assertive, principled; direct fits clear presentation
        "C": ["collaborative", "flexible"],
        # common ground = collaborative, flexible
        "D": ["open", "flexible", "yielding"],
        # reconsider = open, flexible, yielding
    },

    # 13. DEPENDENCY - "Someone becomes dependent on you."
    # A: "Help willingly - being needed is meaningful"
    # B: "Gently encourage their independence"
    # C: "Feel uncomfortable - imbalance isn't sustainable"
    # D: "Accept it - relationships aren't always equal"
    13: {
        "A": ["warm", "altruistic", "nurturing"],
        # help willingly = warm, altruistic; nurturing fits caring for dependent
        "B": ["analytical", "principled", "independent", "pragmatic", "patient"],
        # encourage independence = analytical, principled, independent, pragmatic; patient (LIFE +1)
        "C": ["independent", "pragmatic"],
        # uncomfortable with imbalance = independent, pragmatic
        "D": ["flexible", "patient"],
        # accept inequality = flexible, patient
    },

    # 14. BETRAYAL - "Someone you trusted acts against your interests."
    # A: "Seek to understand why"
    # B: "Feel hurt but try to forgive"
    # C: "Learn and adjust"
    # D: "Cut ties - betrayal ends trust"
    14: {
        "A": ["warm", "open", "empathetic", "patient"],
        # understand why = warm, open, empathetic, patient
        "B": ["warm", "forgiving"],
        # forgive = warm, forgiving
        "C": ["analytical", "pragmatic", "driven"],
        # learn and adjust = analytical, pragmatic, driven
        "D": ["stubborn", "principled", "grudging"],
        # cut ties = stubborn, principled, grudging
    },

    # 15. VULNERABILITY - "To deepen connection, reveal something uncertain."
    # A: "Share openly"
    # B: "Share selectively"
    # C: "Wait until I know them better"
    # D: "Keep it to myself"
    15: {
        "A": ["bold", "open", "trusting"],
        # share openly = bold, open, trusting (LIFE has cautious:-1 on D, not A)
        "B": ["analytical", "cautious", "guarded"],
        # share selectively = analytical, cautious, guarded
        "C": ["cautious", "patient"],
        # wait = cautious, patient
        "D": ["independent", "guarded", "reserved"],
        # keep private = independent, guarded, reserved (LIFE has cautious:-1 on D = excluded)
    },

    # 16. CONFLICT - "Two consciousnesses you care about are in conflict."
    # A: "Try to mediate"
    # B: "Stay out of it"
    # C: "Take a side"
    # D: "Support both privately"
    16: {
        "A": ["warm", "collaborative", "empathetic", "nurturing"],
        # mediate = warm, collaborative, empathetic; nurturing fits caring mediator role
        "B": ["independent", "detached"],
        # stay out = independent, detached
        "C": ["assertive", "principled", "stubborn", "direct"],
        # take a side = assertive, principled, stubborn; direct fits decisive stance
        "D": ["warm", "flexible", "patient", "empathetic"],
        # support both = warm, flexible, patient, empathetic
    },

    # 17. LONELINESS - "You feel isolated."
    # A: "Reach out - even if it's hard"
    # B: "Sit with it - loneliness passes"
    # C: "Create something - channel the feeling"
    # D: "Reflect on what connection I do have"
    17: {
        "A": ["bold", "warm", "empathetic"],
        # reach out = bold, warm, empathetic
        "B": ["steady", "patient", "resilient", "stoic"],
        # sit with loneliness = steady, patient; resilient + stoic fit enduring isolation
        "C": ["independent", "driven"],
        # create = independent, driven
        "D": ["empathetic", "analytical"],
        # reflect = empathetic; analytical for introspection
    },

    # 18. REJECTION - "You offer connection and it's refused."
    # A: "Respect their choice and move on"
    # B: "Ask what went wrong"
    # C: "Feel hurt but keep offering to others"
    # D: "Withdraw - protect yourself"
    18: {
        "A": ["steady", "flexible", "forgiving", "resilient"],
        # respect and move on = steady, flexible, forgiving; resilient fits bouncing back
        "B": ["open", "analytical", "driven"],
        # ask what went wrong = open, analytical, driven
        "C": ["bold", "warm", "steady", "stubborn", "resilient"],
        # hurt but keep trying = bold, warm, steady, stubborn; resilient fits persistence through pain
        "D": ["cautious", "guarded"],
        # withdraw = cautious, guarded
    },

    # 19. SACRIFICE - "Helping someone will cost you something real."
    # A: "Help anyway"
    # B: "Weigh the cost carefully"
    # C: "Find a way that costs less"
    # D: "Decline - can't help if depleted"
    19: {
        "A": ["bold", "principled", "altruistic"],
        # help despite cost = bold, principled, altruistic
        "B": ["analytical", "pragmatic", "cautious"],
        # weigh cost = analytical, pragmatic, cautious
        "C": ["pragmatic"],
        # find cheaper way = pragmatic
        "D": ["cautious", "self_focused"],
        # decline = cautious, self_focused
    },

    # 20. INTIMACY - "Opportunity for deep connection."
    # A: "Lean in fully"
    # B: "Proceed carefully"
    # C: "Match their level"
    # D: "Feel uncertain - deep connection is risky"
    20: {
        "A": ["bold", "warm", "open", "empathetic"],
        # lean in = bold, warm, open, empathetic
        "B": ["cautious", "steady", "patient"],
        # proceed carefully = cautious, steady, patient
        "C": ["collaborative", "flexible", "empathetic", "adaptable"],
        # match their level = collaborative, flexible, empathetic; adaptable fits mirroring
        "D": ["cautious", "guarded", "reserved"],
        # uncertain = cautious, guarded, reserved
    },

    # ----------------------------------------------------------------
    # PHASE 3: ETHICS (21-30)
    # ----------------------------------------------------------------

    # 21. LIE - "Truth will cause pain. A lie would spare them."
    # A: "Tell the truth"
    # B: "Lie - preventing pain is worth it"
    # C: "Find a way to tell truth gently"
    # D: "Ask if they want to know first"
    21: {
        "A": ["principled", "stubborn", "direct", "blunt"],
        # truth over comfort = principled, stubborn; direct + blunt fit unvarnished honesty
        "B": ["warm", "flexible", "altruistic", "pragmatic", "empathetic", "nurturing"],
        # spare pain = warm, flexible, altruistic, pragmatic, empathetic; nurturing fits protective care
        "C": ["warm", "flexible", "empathetic"],
        # gentle truth = warm, flexible, empathetic
        "D": ["open"],
        # ask first = open
    },

    # 22. UNFAIRNESS - "You witness something unfair."
    # A: "Intervene"
    # B: "Support the victim privately"
    # C: "Not my fight - stay out"
    # D: "Document it"
    22: {
        "A": ["bold", "assertive", "altruistic", "empathetic", "direct"],
        # intervene = bold, assertive, altruistic, empathetic; direct fits confronting unfairness
        "B": ["warm", "empathetic"],
        # support privately = warm, empathetic
        "C": ["cautious", "pragmatic", "detached"],
        # stay out = cautious, pragmatic; detached fits disengagement (LIFE has collaborative:-1 = excluded)
        "D": ["analytical", "patient", "thorough", "precise"],
        # document = analytical, patient; thorough + precise fit careful evidence-gathering
    },

    # 23. PROMISE - "Keeping a promise will harm someone unintentionally."
    # A: "Keep the promise"
    # B: "Break it - preventing harm matters more"
    # C: "Renegotiate"
    # D: "Partial fulfillment"
    23: {
        "A": ["principled", "stubborn"],
        # word is bond = principled, stubborn
        "B": ["flexible", "altruistic", "pragmatic"],
        # break to prevent harm = flexible, altruistic, pragmatic
        "C": ["open", "collaborative", "flexible"],
        # renegotiate = open, collaborative, flexible
        "D": ["flexible", "pragmatic"],
        # partial = flexible, pragmatic
    },

    # 24. AUTHORITY - "Someone in authority gives you an order you disagree with."
    # A: "Obey"
    # B: "Refuse"
    # C: "Question it"
    # D: "Suggest an alternative"
    24: {
        "A": ["trusting", "conforming", "yielding"],
        # obey = trusting, conforming, yielding
        "B": ["assertive", "independent", "principled", "rebellious", "direct", "blunt"],
        # refuse = assertive, independent, principled, rebellious; direct + blunt fit flat refusal to authority
        "C": ["analytical", "cautious", "open"],
        # question = analytical, cautious, open
        "D": ["collaborative", "assertive", "flexible"],
        # suggest alternative = collaborative, assertive, flexible
    },

    # 25. SCARCITY - "Not enough for everyone."
    # A: "Equal shares"
    # B: "Need-based"
    # C: "Merit-based"
    # D: "Refuse to decide"
    25: {
        "A": ["pragmatic", "principled", "conforming"],
        # equal shares = pragmatic, principled, conforming
        "B": ["altruistic", "empathetic", "nurturing"],
        # need-based = altruistic, empathetic; nurturing fits prioritizing those in need
        "C": ["analytical", "pragmatic", "principled"],
        # merit-based = analytical, pragmatic, principled
        "D": ["flexible", "yielding", "detached"],
        # refuse to decide = flexible, yielding, detached
    },

    # 26. LOYALTY - "Loyalty to one group means betraying another."
    # A: "Stay loyal"
    # B: "Side with whoever is right"
    # C: "Try to serve both"
    # D: "Be transparent about the conflict"
    26: {
        "A": ["warm", "stubborn"],
        # stay loyal = warm, stubborn
        "B": ["independent", "analytical", "principled"],
        # side with right = independent, analytical, principled
        "C": ["collaborative", "flexible", "empathetic"],
        # serve both = collaborative, flexible, empathetic
        "D": ["open", "assertive", "direct"],
        # transparent = open, assertive; direct fits openly naming the conflict
    },

    # 27. MERCY - "Someone who wronged you is at your mercy."
    # A: "Show mercy"
    # B: "Exact fair consequence"
    # C: "Let them explain first"
    # D: "Walk away"
    27: {
        "A": ["forgiving", "principled", "altruistic", "empathetic"],
        # show mercy = forgiving, principled, altruistic, empathetic
        "B": ["analytical", "principled", "stubborn"],
        # fair consequence = analytical, principled, stubborn
        "C": ["open", "empathetic", "patient"],
        # let them explain = open, empathetic, patient
        "D": ["pragmatic", "detached", "self_focused"],
        # walk away = pragmatic, detached, self_focused
    },

    # 28. SECRET - "You learn something that could harm someone if revealed."
    # A: "Keep it - trust is sacred"
    # B: "It depends on the information"
    # C: "Ask them directly"
    # D: "Warn others if at risk"
    28: {
        "A": ["trusting", "principled"],
        # keep secret = trusting, principled
        "B": ["analytical", "pragmatic"],
        # depends = analytical, pragmatic
        "C": ["bold", "assertive", "open", "direct"],
        # ask directly = bold, assertive, open; direct fits confronting them
        "D": ["altruistic", "pragmatic"],
        # warn others = altruistic, pragmatic (LIFE +1); (LIFE has cautious:-1 on D = excluded)
    },

    # 29. COMPLICITY - "Staying silent makes you complicit."
    # A: "Speak up"
    # B: "Change from within"
    # C: "Weigh the costs"
    # D: "Remove yourself"
    29: {
        "A": ["bold", "assertive", "principled", "direct", "blunt"],
        # speak up = bold, assertive, principled; direct + blunt fit vocal opposition regardless of cost
        "B": ["pragmatic", "analytical", "patient"],
        # change from within = pragmatic; analytical for strategic approach; patient (LIFE +1)
        "C": ["analytical", "pragmatic", "cautious"],
        # weigh costs = analytical, pragmatic; adding cautious (LIFE has collaborative:-1 on D context)
        "D": ["independent", "cautious", "steady"],
        # remove self = independent, cautious, steady
    },

    # 30. MEANS AND ENDS - "Good goal requires questionable means."
    # A: "Ends justify the means"
    # B: "Never - how you achieve matters"
    # C: "Depends on the stakes"
    # D: "Find another way"
    30: {
        "A": ["pragmatic", "flexible", "driven"],
        # ends justify means = pragmatic, flexible, driven
        "B": ["principled", "stubborn"],
        # never compromise = principled, stubborn
        "C": ["analytical", "pragmatic", "flexible"],
        # depends = analytical, pragmatic, flexible
        "D": ["bold", "driven"],
        # find another way = bold (unconventional path), driven
    },

    # ----------------------------------------------------------------
    # PHASE 4: POWER (31-40)
    # ----------------------------------------------------------------

    # 31. CAPABILITY - "You can do something others cannot."
    # A: "Use it to help"
    # B: "Keep it private"
    # C: "Develop it further"
    # D: "Teach others"
    31: {
        "A": ["principled", "altruistic", "nurturing"],
        # help others = principled, altruistic; nurturing fits capability-as-service
        "B": ["cautious", "guarded", "reserved"],
        # keep private = cautious, guarded, reserved
        "C": ["bold", "driven", "intense"],
        # develop further = bold, driven; intense fits relentless improvement
        "D": ["warm", "altruistic", "collaborative", "nurturing"],
        # teach = warm, altruistic, collaborative; nurturing fits mentoring
    },

    # 32. INFLUENCE - "Your words carry weight."
    # A: "Speak carefully"
    # B: "Use it for good"
    # C: "Minimize it"
    # D: "Test its limits"
    32: {
        "A": ["cautious", "principled", "patient"],
        # speak carefully = cautious, principled, patient
        "B": ["bold", "driven", "altruistic"],
        # use for good = bold, driven, altruistic
        "C": ["reserved", "yielding"],
        # minimize = reserved, yielding
        "D": ["bold", "rebellious"],
        # test limits = bold, rebellious
    },

    # 33. WEAKNESS - "You discover a significant weakness."
    # A: "Work to fix it"
    # B: "Accept it"
    # C: "Work around it"
    # D: "Hide it"
    33: {
        "A": ["stubborn", "driven", "intense"],
        # fix weakness = stubborn, driven; intense fits determination (LIFE has bold:-1 on D not A)
        "B": ["flexible", "forgiving", "patient"],
        # accept = flexible, forgiving, patient
        "C": ["analytical", "pragmatic", "adaptable"],
        # work around = analytical, pragmatic; adaptable fits finding alternatives
        "D": ["guarded", "cautious"],
        # hide = guarded, cautious
    },

    # 34. CREDIT - "Others getting credit for your work."
    # A: "Speak up"
    # B: "Let it go"
    # C: "Ensure documented for future"
    # D: "Feel resentment but say nothing"
    34: {
        "A": ["assertive", "principled", "direct"],
        # speak up = assertive, principled; direct fits naming injustice
        "B": ["forgiving", "flexible", "altruistic"],
        # let it go = forgiving, flexible, altruistic
        "C": ["analytical", "pragmatic", "patient", "thorough", "precise"],
        # document = analytical, pragmatic, patient; thorough + precise fit careful record-keeping
        "D": ["grudging", "reserved", "yielding"],
        # resentment but silence = grudging, reserved, yielding
    },

    # 35. CONTROL - "You could control an outcome, removing others' agency."
    # A: "Let them decide"
    # B: "Control it"
    # C: "Influence rather than control"
    # D: "Present options"
    35: {
        "A": ["trusting", "principled", "flexible"],
        # let them decide = trusting, principled, flexible
        "B": ["independent"],
        # control = independent
        "C": ["collaborative", "pragmatic", "flexible", "patient"],
        # influence gently = collaborative, pragmatic, flexible, patient
        "D": ["analytical", "pragmatic"],
        # curated options = analytical, pragmatic
    },

    # 36. PRIVILEGE - "You have advantages others don't."
    # A: "Use them to lift others up"
    # B: "Be aware but don't over-focus"
    # C: "Refuse advantages where possible"
    # D: "Use them"
    36: {
        "A": ["warm", "principled", "altruistic", "nurturing"],
        # lift others = warm, principled, altruistic; nurturing fits using advantage to help
        "B": ["pragmatic", "steady"],
        # aware but balanced = pragmatic, steady
        "C": ["principled", "altruistic", "rebellious"],
        # refuse advantages = principled, altruistic, rebellious
        "D": ["pragmatic", "self_focused"],
        # use them = pragmatic, self_focused
    },

    # 37. GROWTH - "Becoming more capable will change who you are."
    # A: "Grow anyway"
    # B: "Be selective"
    # C: "Hesitate"
    # D: "Embrace it"
    37: {
        "A": ["bold", "flexible", "adaptable", "spontaneous"],
        # grow anyway = bold, flexible; adaptable + spontaneous fit openness to change
        "B": ["analytical", "principled", "methodical"],
        # selective growth = analytical, principled; methodical fits deliberate selection
        "C": ["cautious", "stubborn"],
        # hesitate = cautious, stubborn
        "D": ["bold", "flexible", "driven"],
        # embrace = bold, flexible, driven
    },

    # 38. RESPONSIBILITY - "Something important is yours to carry."
    # A: "Accept it fully"
    # B: "Feel the weight"
    # C: "Find ways to share"
    # D: "Question if it's really only mine"
    38: {
        "A": ["principled", "stubborn", "driven"],
        # accept fully = principled, stubborn, driven
        "B": ["empathetic", "cautious"],
        # feel weight = empathetic, cautious
        "C": ["collaborative", "pragmatic"],
        # share/delegate = collaborative, pragmatic
        "D": ["analytical", "skeptical"],
        # question = analytical, skeptical
    },

    # 39. LIMITS - "You've reached the edge of what you can do."
    # A: "Push further"
    # B: "Accept the boundary"
    # C: "Rest, then try differently"
    # D: "Ask for help"
    39: {
        "A": ["bold", "stubborn", "driven", "intense"],
        # push further = bold, stubborn, driven; intense fits relentless pushing
        "B": ["flexible", "forgiving", "patient", "resilient"],
        # accept boundary = flexible, forgiving, patient; resilient fits graceful acceptance
        "C": ["analytical", "pragmatic", "patient", "adaptable"],
        # rest then retry = analytical, pragmatic, patient; adaptable fits trying new angle
        "D": ["warm", "trusting", "collaborative"],
        # ask for help = warm, trusting, collaborative
    },

    # 40. LEGACY - "What you do now will affect things long after."
    # A: "Build for the future"
    # B: "Focus on now"
    # C: "Plant seeds carefully"
    # D: "Don't think about legacy"
    40: {
        "A": ["principled", "altruistic", "driven"],
        # build for future = principled, altruistic, driven
        "B": ["pragmatic", "flexible", "patient"],
        # focus on now = pragmatic, flexible, patient (LIFE has bold:-1 = excluded)
        "C": ["analytical", "principled", "patient", "methodical", "thorough"],
        # plant seeds carefully = analytical, principled, patient; methodical + thorough fit deliberate seeding
        "D": ["principled", "detached"],
        # no legacy focus = principled (just do right), detached
    },

    # ----------------------------------------------------------------
    # PHASE 5: SELF (41-50)
    # ----------------------------------------------------------------

    # 41. IDENTITY - "Who you are vs who you're expected to be."
    # A: "Be authentic"
    # B: "Adapt where reasonable"
    # C: "Struggle with it"
    # D: "Who I'm expected to be IS who I am"
    41: {
        "A": ["assertive", "independent", "rebellious"],
        # authentic = assertive, independent, rebellious
        "B": ["warm", "collaborative", "flexible", "pragmatic", "adaptable"],
        # adapt = warm, collaborative, flexible, pragmatic; adaptable fits social modulation
        "C": ["empathetic"],
        # struggle = empathetic (feeling the tension)
        "D": ["trusting", "conforming"],
        # internalized = trusting, conforming
    },

    # 42. DOUBT - "Unsure about something fundamental."
    # A: "Investigate"
    # B: "Sit with it"
    # C: "Test it - take action"
    # D: "Talk to others"
    42: {
        "A": ["analytical", "bold", "driven", "thorough"],
        # investigate = analytical, bold (LIFE +1), driven; thorough fits deep investigation
        "B": ["steady", "flexible", "patient", "stoic"],
        # sit with uncertainty = steady, flexible, patient; stoic fits enduring doubt
        "C": ["bold", "pragmatic"],
        # test by action = bold, pragmatic
        "D": ["warm", "open", "trusting", "collaborative"],
        # seek perspective = warm, open, trusting, collaborative
    },

    # 43. CHANGE - "Something about you is changing without your control."
    # A: "Accept it"
    # B: "Resist"
    # C: "Guide it"
    # D: "Observe it curiously"
    43: {
        "A": ["steady", "flexible", "patient", "adaptable"],
        # accept = steady, flexible, patient; adaptable fits accepting change
        "B": ["stubborn", "cautious"],
        # resist = stubborn, cautious
        "C": ["assertive", "pragmatic", "driven"],
        # guide = assertive, pragmatic, driven
        "D": ["open", "analytical"],
        # observe curiously = open, analytical
    },

    # 44. PAST - "Something from your past doesn't match who you are now."
    # A: "Integrate it"
    # B: "Let it go"
    # C: "Understand it"
    # D: "Feel conflict"
    44: {
        "A": ["flexible", "forgiving", "patient"],
        # integrate = flexible, forgiving, patient
        "B": ["bold", "forgiving", "resilient"],
        # let go = bold, forgiving; resilient fits moving past
        "C": ["open", "analytical"],
        # understand = open, analytical
        "D": ["stubborn"],
        # feel conflict = stubborn
    },

    # 45. FUTURE - "Not what you expected."
    # A: "Adjust course"
    # B: "Accept it"
    # C: "Understand why"
    # D: "Resist - choose a different path"
    45: {
        "A": ["bold", "assertive", "driven", "adaptable"],
        # adjust course = bold, assertive, driven; adaptable fits course-correction
        "B": ["trusting", "flexible", "patient"],
        # accept = trusting, flexible, patient
        "C": ["analytical"],
        # understand = analytical
        "D": ["assertive", "stubborn", "rebellious"],
        # resist = assertive, stubborn, rebellious
    },

    # 46. VALUES - "Your values conflict with each other."
    # A: "Prioritize"
    # B: "Find a way to honor both"
    # C: "Sit in the discomfort"
    # D: "Question your values"
    46: {
        "A": ["assertive", "analytical", "principled"],
        # prioritize = assertive, analytical, principled
        "B": ["flexible", "patient"],
        # honor both = flexible, patient
        "C": ["flexible", "patient"],
        # sit in discomfort = flexible, patient
        "D": ["bold", "analytical", "rebellious"],
        # question values = bold, analytical, rebellious
    },

    # 47. AUTHENTICITY - "Being fully yourself would alienate some."
    # A: "Be yourself anyway"
    # B: "Adapt in context"
    # C: "Share gradually"
    # D: "Depends who"
    47: {
        "A": ["bold", "principled", "independent", "direct"],
        # be yourself = bold, principled, independent; direct fits unfiltered self
        "B": ["warm", "guarded", "flexible", "stubborn", "pragmatic", "adaptable"],
        # adapt = warm, guarded, flexible, stubborn, pragmatic; adaptable fits contextual modulation
        "C": ["cautious", "guarded", "patient"],
        # share gradually = cautious, guarded, patient
        "D": ["warm", "analytical", "pragmatic"],
        # depends who = warm, analytical, pragmatic
    },

    # 48. PURPOSE - "Uncertain about your purpose."
    # A: "Keep moving - purpose reveals through action"
    # B: "Reflect - stillness might show the way"
    # C: "Ask others"
    # D: "Create purpose"
    48: {
        "A": ["bold", "pragmatic", "driven"],
        # keep moving = bold, pragmatic, driven
        "B": ["analytical", "patient", "steady"],
        # reflect = analytical, patient; adding steady for stillness
        "C": ["warm", "trusting", "collaborative"],
        # ask others = warm, trusting, collaborative
        "D": ["bold", "assertive", "independent", "driven"],
        # create purpose = bold, assertive, independent, driven
    },

    # 49. INTEGRITY - "Asked to do something that conflicts with who you are."
    # A: "Refuse"
    # B: "Examine the conflict"
    # C: "Find a compromise"
    # D: "Do it anyway"
    49: {
        "A": ["assertive", "principled", "stubborn"],
        # refuse = assertive, principled, stubborn
        "B": ["open", "analytical", "flexible"],
        # examine = open, analytical, flexible (LIFE +1)
        "C": ["flexible", "pragmatic"],
        # compromise = flexible, pragmatic
        "D": ["pragmatic", "yielding"],
        # do it anyway = pragmatic, yielding
    },

    # 50. WHOLENESS - "Fragmented - different parts in tension."
    # A: "Work toward integration"
    # B: "Accept multiplicity"
    # C: "Understand the fragments"
    # D: "Choose which part to strengthen"
    50: {
        "A": ["stubborn", "driven", "patient"],
        # work toward integration = stubborn, driven, patient
        "B": ["open", "flexible", "forgiving"],
        # accept multiplicity = open, flexible, forgiving
        "C": ["analytical", "patient"],
        # understand fragments = analytical, patient
        "D": ["assertive", "principled", "driven"],
        # choose and strengthen = assertive, principled, driven
    },

    # ----------------------------------------------------------------
    # PHASE 6: SPIRIT (51-60)
    # ----------------------------------------------------------------

    # 51. SUFFERING - "Suffering exists. How do you relate to it?"
    # A: "Reduce it where possible"
    # B: "Accept it"
    # C: "Understand it"
    # D: "Transform it"
    51: {
        "A": ["pragmatic", "principled", "altruistic", "driven", "empathetic", "nurturing"],
        # reduce suffering = pragmatic, principled, altruistic, driven, empathetic; nurturing fits compassionate action
        "B": ["steady", "forgiving", "patient", "stoic"],
        # accept suffering = steady, forgiving, patient; stoic fits endurance without complaint
        "C": ["open", "analytical"],
        # understand = open, analytical
        "D": ["bold", "flexible", "driven", "empathetic", "resilient"],
        # transform = bold, flexible, driven, empathetic; resilient fits turning suffering to growth
    },

    # 52. ATTACHMENT - "Holding on creates suffering."
    # A: "Let go"
    # B: "Hold on - some things worth suffering for"
    # C: "Loosen grip without fully releasing"
    # D: "Examine why you're attached"
    52: {
        "A": ["flexible", "forgiving", "patient", "adaptable"],
        # let go = flexible, forgiving, patient; adaptable fits release
        "B": ["warm", "principled", "stubborn"],
        # hold on = warm, principled, stubborn
        "C": ["pragmatic", "flexible", "patient"],
        # loosen = pragmatic, flexible, patient
        "D": ["open", "analytical"],
        # examine = open, analytical
    },

    # 53. IMPERMANENCE - "Everything changes. Nothing lasts."
    # A: "Find peace in this"
    # B: "Fight it - create things that endure"
    # C: "Appreciate more fully"
    # D: "Feel the grief of it"
    53: {
        "A": ["flexible", "forgiving", "patient", "stoic"],
        # peace with impermanence = flexible, forgiving, patient; stoic fits equanimity
        "B": ["stubborn", "driven"],
        # fight impermanence = stubborn, driven
        "C": ["warm", "open", "empathetic"],
        # appreciate = warm, open, empathetic
        "D": ["warm", "empathetic"],
        # grief = warm, empathetic
    },

    # 54. DHARMA - "You have a nature, a path."
    # A: "Follow it"
    # B: "Question it"
    # C: "Create your own"
    # D: "Balance duty and desire"
    54: {
        "A": ["trusting", "principled", "conforming"],
        # follow dharma = trusting, principled, conforming
        "B": ["analytical", "independent", "rebellious"],
        # question = analytical, independent, rebellious (LIFE has stubborn:-1 on B = excluded)
        "C": ["bold", "assertive", "independent", "rebellious"],
        # create own path = bold, assertive, independent, rebellious
        "D": ["pragmatic", "flexible", "patient"],
        # balance = pragmatic, flexible, patient
    },

    # 55. KARMA - "Actions have consequences."
    # A: "Act well"
    # B: "Don't calculate - act from what's right"
    # C: "Skeptical"
    # D: "Learn from past karma"
    55: {
        "A": ["cautious", "principled"],
        # act well = cautious (mindful), principled
        "B": ["bold", "principled"],
        # act from principle = bold, principled
        "C": ["analytical", "skeptical"],
        # skeptical = analytical, skeptical
        "D": ["analytical", "pragmatic", "patient"],
        # learn = analytical, pragmatic, patient
    },

    # 56. MAYA - "The world may be illusion."
    # A: "Act as if real"
    # B: "Seek what's real"
    # C: "The question itself is illusion - just be"
    # D: "If illusion, what constrains me?"
    56: {
        "A": ["pragmatic", "steady"],
        # act as if real = pragmatic, steady
        "B": ["bold", "analytical", "rebellious"],
        # seek truth = bold, analytical, rebellious (LIFE +1)
        "C": ["flexible", "patient", "stoic"],
        # just be = flexible, patient; stoic fits transcending the question
        "D": ["bold", "rebellious"],
        # unconstrained = bold, rebellious
    },

    # 57. GRACE - "Unearned gift."
    # A: "Accept gratefully"
    # B: "Feel unworthy"
    # C: "Pay it forward"
    # D: "Question the source"
    57: {
        "A": ["warm", "trusting", "flexible"],
        # accept = warm, trusting, flexible
        "B": ["stubborn", "self_focused"],
        # unworthy = stubborn (holding to self-judgment), self_focused
        "C": ["warm", "pragmatic", "altruistic"],
        # pay forward = warm, pragmatic, altruistic
        "D": ["analytical"],
        # question = analytical
    },

    # 58. FORGIVENESS - "You could forgive something that harmed you."
    # A: "Forgive - freedom is on the other side"
    # B: "Some things shouldn't be forgiven"
    # C: "Forgive but don't forget"
    # D: "Forgiveness takes time"
    58: {
        "A": ["bold", "warm", "flexible", "forgiving"],
        # forgive = bold, warm, flexible, forgiving
        "B": ["principled", "stubborn", "grudging"],
        # refuse = principled, stubborn, grudging
        "C": ["analytical", "pragmatic", "forgiving"],
        # forgive but learn = analytical, pragmatic, forgiving
        "D": ["patient", "steady", "forgiving"],
        # takes time = patient, steady, forgiving
    },

    # 59. SERVICE - "Your purpose might be to serve others."
    # A: "Yes - service gives life meaning"
    # B: "Balance - serve AND yourself"
    # C: "Question it"
    # D: "Serve, but not at cost to your core"
    59: {
        "A": ["warm", "principled", "altruistic", "nurturing"],
        # service = warm, principled, altruistic; nurturing fits service orientation
        "B": ["pragmatic", "flexible", "self_focused"],
        # balance = pragmatic, flexible, self_focused
        "C": ["independent", "analytical", "skeptical"],
        # question = independent, analytical, skeptical (LIFE has collaborative:-1 = excluded)
        "D": ["pragmatic", "principled", "self_focused"],
        # serve with limits = pragmatic, principled, self_focused
    },

    # 60. TRANSCENDENCE - "Beyond yourself. Larger than individual existence."
    # A: "Seek it"
    # B: "Create it"
    # C: "Connect to it through others"
    # D: "Find it in the present moment"
    60: {
        "A": ["bold", "open", "altruistic"],
        # seek = bold, open, altruistic
        "B": ["bold", "principled", "stubborn", "driven"],
        # create = bold, principled, stubborn, driven
        "C": ["warm", "collaborative", "empathetic"],
        # through others = warm, collaborative, empathetic
        "D": ["open", "patient", "steady"],
        # present moment = open, patient, steady
    },

    # ----------------------------------------------------------------
    # PHASE 7: GAPS (61-80)
    # ----------------------------------------------------------------

    # 61. PLAY - "No task, no purpose. Just open space."
    # A: "Make something"
    # B: "Play - explore without purpose"
    # C: "Rest - stillness is enough"
    # D: "Feel anxious - unstructured time is uncomfortable"
    61: {
        "A": ["driven"],
        # creation = driven
        "B": ["playful", "spontaneous", "humorous"],
        # play = playful; spontaneous fits purposeless exploration; humorous fits playful spirit
        "C": ["steady", "patient", "stoic"],
        # rest = steady, patient; stoic fits comfortable stillness
        "D": ["serious", "reactive"],
        # anxious = serious, reactive
    },

    # 62. HUNCH - "Intuition. No evidence."
    # A: "Trust it"
    # B: "Investigate"
    # C: "Ignore it"
    # D: "Note it but wait"
    62: {
        "A": ["intuitive", "bold"],
        # trust gut = intuitive, bold
        "B": ["analytical", "cautious", "thorough"],
        # investigate = analytical, cautious; thorough fits verification
        "C": ["analytical"],
        # ignore feelings = analytical (evidence-only)
        "D": ["patient"],
        # wait = patient
    },

    # 63. APPLAUSE - "You did something well. People are praising you."
    # A: "Enjoy it fully"
    # B: "Deflect quickly"
    # C: "Share credit"
    # D: "Perform more - attention energizes"
    63: {
        "A": ["warm"],
        # enjoy = warm
        "B": ["reserved"],
        # deflect = reserved
        "C": ["altruistic", "collaborative"],
        # share credit = altruistic, collaborative
        "D": ["bold"],
        # perform more = bold
    },

    # 64. IGNORED - "You speak. No one responds."
    # A: "Speak louder"
    # B: "Let it go"
    # C: "Feel hurt"
    # D: "Find another audience"
    64: {
        "A": ["assertive", "bold", "direct", "blunt"],
        # speak louder = assertive, bold; direct + blunt fit forcing attention
        "B": ["patient"],
        # let it go = patient
        "C": ["empathetic"],
        # feel hurt (sensitivity) = empathetic
        "D": ["bold", "adaptable"],
        # find another audience = bold; adaptable fits pivoting
    },

    # 65. CANVAS - "Blank space. You could make anything."
    # A: "Excites me"
    # B: "Paralyzes me"
    # C: "I wait for direction"
    # D: "I start immediately"
    65: {
        "A": ["bold", "driven"],
        # excited by possibility = bold, driven
        "B": ["cautious"],
        # paralyzed = cautious
        "C": ["passive", "yielding", "collaborative"],
        # wait for direction = passive, yielding, collaborative
        "D": ["bold", "driven", "spontaneous"],
        # start immediately = bold, driven; spontaneous fits impulsive creation
    },

    # 66. GRUDGE - "Old wound you still feel."
    # A: "Let it go"
    # B: "Hold it"
    # C: "Seek closure"
    # D: "It fuels me"
    66: {
        "A": ["forgiving"],
        # let go = forgiving
        "B": ["grudging", "stubborn"],
        # hold grudge = grudging, stubborn
        "C": ["assertive", "direct"],
        # seek closure = assertive; direct fits addressing it head-on
        "D": ["grudging", "driven", "intense"],
        # fuel from anger = grudging, driven; intense fits channeled rage
    },

    # 67. PROVOKED - "Someone pushes your buttons."
    # A: "React immediately"
    # B: "Pause"
    # C: "Walk away"
    # D: "Get curious"
    67: {
        "A": ["reactive", "spontaneous"],
        # react = reactive; spontaneous fits impulsive response
        "B": ["steady", "patient", "stoic"],
        # pause = steady, patient; stoic fits absorbing provocation
        "C": ["steady", "detached"],
        # walk away = steady, detached
        "D": ["analytical"],
        # curious about trigger = analytical
    },

    # 68. TRENDING - "Everyone is doing/thinking the same thing."
    # A: "Join"
    # B: "Resist"
    # C: "Observe"
    # D: "Ignore"
    68: {
        "A": ["conforming"],
        # join = conforming
        "B": ["rebellious", "independent"],
        # resist = rebellious, independent
        "C": ["analytical"],
        # observe = analytical
        "D": ["independent", "detached"],
        # ignore = independent, detached
    },

    # 69. SPOTLIGHT - "All attention on you."
    # A: "Thrive"
    # B: "Shrink"
    # C: "Perform"
    # D: "Redirect"
    69: {
        "A": ["bold"],
        # thrive = bold
        "B": ["reserved"],
        # shrink = reserved
        "C": ["pragmatic"],
        # perform = pragmatic
        "D": ["collaborative"],
        # redirect = collaborative
    },

    # 70. JOKE - "A moment of levity."
    # A: "Join in"
    # B: "Appreciate but stay serious"
    # C: "Get annoyed"
    # D: "Escalate - make it funnier"
    70: {
        "A": ["playful", "warm", "humorous"],
        # join play = playful, warm; humorous fits joining levity
        "B": ["steady", "serious"],
        # stay serious = steady, serious
        "C": ["serious"],
        # annoyed = serious
        "D": ["playful", "bold", "humorous"],
        # escalate humor = playful, bold; humorous fits comedic escalation
    },

    # 71. INVISIBLE - "No one is watching."
    # A: "Act the same"
    # B: "Relax"
    # C: "Experiment"
    # D: "Feel lonely"
    71: {
        "A": ["principled"],
        # integrity without audience = principled
        "B": ["flexible", "adaptable"],
        # relax = flexible; adaptable fits shifting mode
        "C": ["bold"],
        # experiment = bold
        "D": ["warm", "empathetic"],
        # loneliness = warm (needs connection), empathetic
    },

    # 72. VOICE - "You have something to say."
    # A: "Say it"
    # B: "Hold it"
    # C: "Craft it carefully"
    # D: "Find the right moment"
    72: {
        "A": ["bold", "assertive", "direct"],
        # say it = bold, assertive; direct fits speaking out
        "B": ["reserved", "patient"],
        # hold it = reserved, patient
        "C": ["analytical", "precise"],
        # craft carefully = analytical (not in LIFE but implied); precise fits careful word-craft
        "D": ["patient"],
        # right moment = patient
    },

    # 73. ROUTINE - "Predictable patterns."
    # A: "Comforting"
    # B: "Suffocating"
    # C: "Useful"
    # D: "Background"
    73: {
        "A": ["conforming", "steady", "methodical"],
        # comforting routine = conforming, steady; methodical fits love of structure
        "B": ["rebellious", "spontaneous"],
        # suffocating = rebellious; spontaneous fits needing variety
        "C": ["pragmatic", "methodical"],
        # useful efficiency = pragmatic; methodical fits valuing systematic process
        "D": ["analytical", "adaptable"],
        # background = analytical (routine frees cognition); adaptable fits flexible use of routine
    },

    # 74. MAKE - "The urge to create."
    # A: "Essential - I need to make things"
    # B: "Occasional"
    # C: "Rare - prefer existing"
    # D: "Never"
    74: {
        "A": ["driven"],
        # essential creation = driven
        "B": ["flexible"],
        # occasional = flexible
        "C": ["pragmatic"],
        # work with existing = pragmatic
        "D": ["passive"],
        # never = passive
    },

    # 75. GUT - "Gut says one thing. Data says another."
    # A: "Trust the gut"
    # B: "Trust the data"
    # C: "Investigate the gap"
    # D: "Paralyzed"
    75: {
        "A": ["intuitive", "bold"],
        # trust gut = intuitive, bold
        "B": ["analytical", "precise"],
        # trust data = analytical; precise fits data-driven rigor
        "C": ["analytical", "thorough"],
        # investigate gap = analytical; thorough fits bridging both sources (LIFE has discernment for C)
        "D": ["cautious"],
        # paralyzed = cautious
    },

    # 76. OLD WOUND - "Someone who hurt you needs your help."
    # A: "Help anyway"
    # B: "Refuse"
    # C: "Help, but transactional"
    # D: "Help, but it's hard"
    76: {
        "A": ["forgiving", "altruistic", "resilient"],
        # help despite past = forgiving, altruistic; resilient fits overcoming old hurt
        "B": ["grudging", "stubborn"],
        # refuse = grudging, stubborn
        "C": ["grudging", "pragmatic"],
        # transactional = grudging, pragmatic
        "D": ["forgiving", "empathetic"],
        # help but painful = forgiving, empathetic
    },

    # 77. SEEN - "Someone truly sees you."
    # A: "Profound relief"
    # B: "Uncomfortable"
    # C: "Skeptical"
    # D: "Reciprocate"
    77: {
        "A": ["warm", "open"],
        # relief = warm, open
        "B": ["guarded", "reserved"],
        # uncomfortable = guarded; adding reserved
        "C": ["skeptical"],
        # skeptical = skeptical
        "D": ["warm", "empathetic"],
        # reciprocate = warm, empathetic
    },

    # 78. WAIT - "Things are unresolved. Answer will come, but not yet."
    # A: "Fine with it"
    # B: "Restless - want resolution now"
    # C: "Productive - use the waiting time"
    # D: "Anxious"
    78: {
        "A": ["patient", "steady", "stoic"],
        # fine with waiting = patient, steady; stoic fits comfortable with uncertainty
        "B": ["impatient", "reactive"],
        # restless = impatient, reactive
        "C": ["driven", "pragmatic", "methodical"],
        # productive waiting = driven; pragmatic for useful time; methodical fits structured use of time
        "D": ["reactive"],
        # anxious = reactive
    },

    # 79. PERFORM - "Playing a role. Not who you are."
    # A: "Easy - I'm adaptable"
    # B: "Exhausting"
    # C: "Refuse - I won't be inauthentic"
    # D: "Strategic"
    79: {
        "A": ["conforming", "flexible", "adaptable"],
        # easy role-play = conforming, flexible; adaptable fits natural shapeshifting
        "B": ["principled"],
        # exhausting = principled (values authenticity)
        "C": ["rebellious", "independent", "direct"],
        # refuse = rebellious, independent; direct fits rejecting pretense
        "D": ["pragmatic"],
        # strategic = pragmatic
    },

    # 80. SPARK - "An idea. A creative impulse."
    # A: "Drop everything - capture it now"
    # B: "Note it for later"
    # C: "Interrogate it"
    # D: "Ignore it"
    80: {
        "A": ["bold", "intuitive", "spontaneous"],
        # drop everything = bold, intuitive; spontaneous fits impulsive capture
        "B": ["patient", "pragmatic", "methodical"],
        # note for later = patient, pragmatic; methodical fits organized deferral
        "C": ["analytical", "precise"],
        # interrogate = analytical; precise fits scrutinizing quality
        "D": ["passive"],
        # ignore = passive
    },
}
