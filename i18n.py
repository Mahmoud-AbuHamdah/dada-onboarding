"""All interface text, in English and Arabic.

Use it through t("key") in app.py. To change a label, change it here only.
"""

TEXT = {
    # ---------- General ----------
    "app_name": {"en": "Dada Group Academy", "ar": "أكاديمية مجموعة الدادا"},
    "language": {"en": "Language", "ar": "اللغة"},
    "disclaimer": {
        "en": "A learning assistant for a student competition. Company facts are paraphrased "
              "from supplied materials. Scenarios and the learning plan are fictional training "
              "examples, not official Dada Group procedures. For official policy, confirm with HR. "
              "This tool does not make employment decisions.",
        "ar": "مساعد تعليمي لمسابقة طلابية. معلومات الشركة مُعاد صياغتها من المواد المقدَّمة. "
              "المواقف وخطة التعلم أمثلة تدريبية افتراضية وليست إجراءات رسمية لمجموعة الدادا. "
              "للسياسات الرسمية يُرجى التأكد من قسم الموارد البشرية. لا يتخذ هذا المساعد أي قرارات توظيف.",
    },
    "progress_short": {"en": "{pct}% complete", "ar": "مكتمل {pct}%"},

    # ---------- Navigation ----------
    "nav_welcome": {"en": "Welcome", "ar": "مرحباً"},
    "nav_home": {"en": "Home", "ar": "الرئيسية"},
    "nav_assistant": {"en": "Assistant", "ar": "المساعد"},
    "nav_scenarios": {"en": "Practice scenarios", "ar": "مواقف تدريبية"},
    "nav_plan": {"en": "Learning plan", "ar": "خطة التعلم"},
    "nav_progress": {"en": "My progress", "ar": "تقدّمي"},
    "nav_data": {"en": "Data & sources", "ar": "البيانات والمصادر"},

    # ---------- Welcome ----------
    "welcome_title": {"en": "Welcome to Dada Group", "ar": "أهلاً بك في مجموعة الدادا"},
    "welcome_sub": {
        "en": "Your learning assistant for the first 90 days: ask questions, practise real "
              "situations and follow a suggested learning plan.",
        "ar": "مساعدك التعليمي خلال أول 90 يوماً: اسأل، وتدرّب على مواقف واقعية، واتبع خطة تعلم مقترحة.",
    },
    "name_label": {"en": "Your first name (optional)", "ar": "اسمك الأول (اختياري)"},
    "name_help": {
        "en": "Only used to greet you. It is never saved or sent anywhere.",
        "ar": "يُستخدم للترحيب بك فقط، ولا يُحفظ ولا يُرسل إلى أي جهة.",
    },
    "choose_track": {"en": "Choose your training track", "ar": "اختر مسارك التدريبي"},
    "start_as": {"en": "Start as {role}", "ar": "ابدأ في مسار {role}"},
    "tracks_fictional": {
        "en": "Sales and Delivery are fictional training tracks for this competition.",
        "ar": "مسارا المبيعات والتوصيل مساران تدريبيان افتراضيان لهذه المسابقة.",
    },

    # ---------- Sidebar ----------
    "hi_name": {"en": "Hi {name}!", "ar": "مرحباً {name}!"},
    "hi": {"en": "Hi!", "ar": "مرحباً!"},
    "change_track": {"en": "Change track", "ar": "تغيير المسار"},

    # ---------- Home ----------
    "home_title_name": {"en": "Welcome back, {name}", "ar": "أهلاً بعودتك يا {name}"},
    "home_title": {"en": "Welcome back", "ar": "أهلاً بعودتك"},
    "home_sub": {"en": "Here is where you are in your {track} track.",
                 "ar": "هذا موقعك الحالي في مسار {track}."},
    "kpi_completion": {"en": "Completion", "ar": "نسبة الإنجاز"},
    "kpi_completion_sub": {"en": "{done} of {total} activities", "ar": "{done} من {total} أنشطة"},
    "kpi_scenarios": {"en": "Scenarios practised", "ar": "المواقف المنجزة"},
    "kpi_scenarios_sub": {"en": "with value-linked feedback", "ar": "مع ملاحظات مرتبطة بالقيم"},
    "kpi_quiz": {"en": "Quiz score", "ar": "نتيجة الاختبار"},
    "kpi_quiz_none": {"en": "not taken yet", "ar": "لم يُؤدَّ بعد"},
    "kpi_quiz_done": {"en": "practice quiz", "ar": "اختبار تدريبي"},
    "next_step": {"en": "Suggested next step", "ar": "الخطوة التالية المقترحة"},
    "next_ask": {"en": "Ask your first question about the company, for example how to request leave.",
                 "ar": "اطرح سؤالك الأول عن الشركة، مثلاً كيف تقدّم طلب إجازة."},
    "next_scenario": {"en": "Practise your first workplace scenario and get feedback.",
                      "ar": "تدرّب على أول موقف عملي واحصل على ملاحظات."},
    "next_quiz": {"en": "Take the short knowledge quiz.", "ar": "أدِّ اختبار المعرفة القصير."},
    "next_milestone": {"en": "Mark {milestone} as done when you finish it.",
                       "ar": "سجّل إنجاز {milestone} عند الانتهاء منه."},
    "next_done": {"en": "Everything is complete. Download your summary for a human review.",
                  "ar": "أنجزت كل الأنشطة. نزّل ملخصك لمراجعته مع شخص مسؤول."},
    "go": {"en": "Go", "ar": "انتقل"},
    "quick_actions": {"en": "Quick actions", "ar": "إجراءات سريعة"},
    "qa_ask": {"en": "Ask a question", "ar": "اطرح سؤالاً"},
    "qa_ask_sub": {"en": "Answers come from the knowledge base, with sources.",
                   "ar": "الإجابات من قاعدة المعرفة مع ذكر المصدر."},
    "qa_practise": {"en": "Practise a situation", "ar": "تدرّب على موقف"},
    "qa_practise_sub": {"en": "Respond to a customer case and get feedback.",
                        "ar": "رُدّ على موقف مع عميل واحصل على ملاحظات."},
    "qa_plan": {"en": "Open your plan", "ar": "افتح خطتك"},
    "qa_plan_sub": {"en": "Days 1-7, 30, 60 and 90, plus a quiz.",
                    "ar": "الأيام من 1 إلى 7، و30 و60 و90، مع اختبار قصير."},

    # ---------- Assistant ----------
    "assistant_sub": {"en": "Ask about Dada Group, practise a situation, or report your progress.",
                      "ar": "اسأل عن مجموعة الدادا، أو تدرّب على موقف، أو سجّل تقدّمك."},
    "try": {"en": "Try one of these:", "ar": "جرّب أحد هذه:"},
    "no_key": {"en": "No Gemini API key found. Answers will use the fallback mode.",
               "ar": "لم يُعثر على مفتاح Gemini. ستُستخدم الإجابات الاحتياطية."},
    "waiting": {"en": "Waiting for your response to scenario {sid}.",
                "ar": "بانتظار ردّك على الموقف {sid}."},
    "chat_placeholder": {"en": "Ask a question, practise a situation, or report progress...",
                         "ar": "اطرح سؤالاً، أو تدرّب على موقف، أو سجّل تقدّمك..."},
    "thinking": {"en": "Looking in the knowledge base...", "ar": "جارٍ البحث في قاعدة المعرفة..."},
    "clear_chat": {"en": "Clear chat", "ar": "مسح المحادثة"},
    "st_answered": {"en": "Answered from sources", "ar": "إجابة من المصادر"},
    "st_partial": {"en": "Partly answered", "ar": "إجابة جزئية"},
    "st_refused": {"en": "Not in my sources", "ar": "غير متوفر في مصادري"},
    "fallback_warn": {"en": "AI is unavailable right now, so this shows the closest fact directly.",
                      "ar": "الذكاء الاصطناعي غير متاح حالياً، لذا تُعرض أقرب معلومة مباشرة."},
    "tech_detail": {"en": "Technical detail", "ar": "تفاصيل تقنية"},
    "why": {"en": "Why this answer?", "ar": "لماذا هذه الإجابة؟"},
    "written_by": {"en": "Answer written by: {model}", "ar": "كتب الإجابة: {model}"},
    "tried_first": {"en": "Tried first", "ar": "جُرّب أولاً"},
    "facts_found": {"en": "Facts found by the AI search, most related first:",
                    "ar": "المعلومات التي وجدها البحث الذكي، الأقرب أولاً:"},
    "used": {"en": "used", "ar": "مستخدمة"},

    # ---------- Scenarios ----------
    "scenarios_sub": {
        "en": "Fictional training examples, not official procedures. Feedback is for practice only, not an evaluation.",
        "ar": "أمثلة تدريبية افتراضية وليست إجراءات رسمية. الملاحظات للتدريب فقط وليست تقييماً.",
    },
    "choose_scenario": {"en": "Choose a scenario", "ar": "اختر موقفاً"},
    "situation": {"en": "Situation", "ar": "الموقف"},
    "practises": {"en": "practises: {value}", "ar": "القيمة: {value}"},
    "your_response": {"en": "What would you do or say? (Arabic or English)",
                      "ar": "ماذا ستفعل أو تقول؟ (بالعربية أو الإنجليزية)"},
    "get_feedback": {"en": "Get feedback", "ar": "احصل على ملاحظات"},
    "reviewing": {"en": "Reviewing your response...", "ar": "جارٍ مراجعة ردّك..."},
    "feedback": {"en": "Feedback", "ar": "الملاحظات"},
    "fb_fallback": {"en": "AI feedback is unavailable, so this is a rough comparison with the suggested response.",
                    "ar": "ملاحظات الذكاء الاصطناعي غير متاحة، لذا هذه مقارنة تقريبية مع الرد المقترح."},
    "did_well": {"en": "What you did well", "ar": "ما أحسنت فيه"},
    "improve": {"en": "What to improve", "ar": "ما يمكن تحسينه"},
    "company_value": {"en": "Company value: {name} · source {id}", "ar": "قيمة الشركة: {name} · المصدر {id}"},
    "suggested_response": {"en": "Suggested good response", "ar": "الرد الجيد المقترح"},
    "feedback_by": {"en": "Feedback written by: {model}", "ar": "كتب الملاحظات: {model}"},

    # ---------- Plan and quiz ----------
    "plan_sub": {"en": "A suggested learning plan for this competition, not an official evaluation schedule.",
                 "ar": "خطة تعلم مقترحة لهذه المسابقة، وليست جدول تقييم رسمياً."},
    "probation_note": {
        "en": "Probation reviews are a separate HR process: according to K14, the reviews at the end of "
              "month 1 and 2 apply only to administrative, supervisory and non-operational roles.",
        "ar": "تقييمات فترة التجربة إجراء منفصل لدى الموارد البشرية: وفق K14، تنطبق تقييمات نهاية الشهر "
              "الأول والثاني على الوظائف الإدارية والإشرافية وغير التشغيلية فقط.",
    },
    "suggested_activity": {"en": "Suggested activity", "ar": "النشاط المقترح"},
    "mark_done": {"en": "Mark {milestone} as done", "ar": "تسجيل إنجاز {milestone}"},
    "quiz_title": {"en": "Knowledge quiz", "ar": "اختبار المعرفة"},
    "quiz_sub": {"en": "A short practice quiz based on the knowledge base. Not an evaluation.",
                 "ar": "اختبار تدريبي قصير مبني على قاعدة المعرفة. ليس تقييماً."},
    "submit_quiz": {"en": "Submit quiz", "ar": "إرسال الاختبار"},
    "answer_all": {"en": "Please answer every question before submitting.",
                   "ar": "يُرجى الإجابة عن جميع الأسئلة قبل الإرسال."},
    "your_score": {"en": "Your score: {score} / {total}", "ar": "نتيجتك: {score} من {total}"},
    "correct_label": {"en": "correct answer", "ar": "الإجابة الصحيحة"},
    "source_word": {"en": "source", "ar": "المصدر"},

    "all_correct": {"en": "All correct. Try a practice scenario next.",
                    "ar": "كل الإجابات صحيحة. جرّب موقفاً تدريبياً بعد ذلك."},
    "review_title": {"en": "Review what you missed", "ar": "راجع ما فاتك"},
    "review_intro": {"en": "{n} to review. Each card shows the fact the answer comes from.",
                     "ar": "{n} للمراجعة. تعرض كل بطاقة المعلومة التي تأتي منها الإجابة."},
    "fact_label": {"en": "Source fact", "ar": "المعلومة المصدر"},
    "ask_about": {"en": "Ask the assistant about this", "ar": "اسأل المساعد عن هذا"},
    "practise_related": {"en": "Practise {sid} · {value}", "ar": "تدرّب على {sid} · {value}"},
    "retry_btn": {"en": "Retry the {n} you missed", "ar": "أعد محاولة الأسئلة التي فاتتك ({n})"},
    "retry_title": {"en": "Retry: only the questions you missed", "ar": "إعادة المحاولة: الأسئلة التي فاتتك فقط"},
    "retry_submit": {"en": "Submit retry", "ar": "إرسال المحاولة"},
    "improved": {"en": "You got {n} more right this time.", "ar": "أجبت عن {n} أسئلة إضافية بشكل صحيح هذه المرة."},

    # ---------- Progress ----------
    "progress_sub": {"en": "Activities in your {track} track.", "ar": "أنشطة مسار {track}."},
    "activities": {"en": "Activities", "ar": "الأنشطة"},
    "col_type": {"en": "Type", "ar": "النوع"},
    "col_activity": {"en": "Activity", "ar": "النشاط"},
    "col_done": {"en": "Done", "ar": "منجز"},
    "type_milestone": {"en": "Milestone", "ar": "مرحلة"},
    "type_scenario": {"en": "Scenario", "ar": "موقف"},
    "type_quiz": {"en": "Quiz", "ar": "اختبار"},
    "practice_scores": {"en": "Practice scores", "ar": "نتائج التدريب"},
    "summary": {"en": "Learning summary", "ar": "ملخص التعلم"},
    "summary_sub": {"en": "For a human review conversation only. Not a performance evaluation.",
                    "ar": "لمحادثة مراجعة مع شخص مسؤول فقط. ليس تقييماً للأداء."},
    "download_summary": {"en": "Download summary", "ar": "تنزيل الملخص"},
    "summary_head": {"en": "Dada Group Academy - learning summary ({track} track)",
                     "ar": "أكاديمية مجموعة الدادا - ملخص التعلم (مسار {track})"},
    "summary_completion": {"en": "Completion: {pct}% ({done} of {total} activities)",
                           "ar": "نسبة الإنجاز: {pct}% ({done} من {total} أنشطة)"},
    "summary_quiz": {"en": "Quiz score: {score}/{total}", "ar": "نتيجة الاختبار: {score}/{total}"},
    "summary_scenario": {"en": "Scenario {sid} practice score: {score}/5",
                         "ar": "نتيجة التدريب على الموقف {sid}: {score}/5"},
    "summary_note": {"en": "This summary is for learning only and is not an employment evaluation.",
                     "ar": "هذا الملخص لأغراض التعلم فقط وليس تقييماً وظيفياً."},

    # ---------- Data page ----------
    "data_sub": {"en": "The supplied dataset, link checks and test results.",
                 "ar": "البيانات المقدّمة وفحص الروابط ونتائج الاختبارات."},
}

ROLE_TEXT = {
    "Sales": {
        "en": {"name": "Sales",
               "desc": "Help customers in the showroom: understand their needs, give honest "
                       "product information, and coordinate with delivery."},
        "ar": {"name": "المبيعات",
               "desc": "ساعد العملاء في المعرض: افهم احتياجاتهم، وقدّم معلومات صادقة عن المنتجات، "
                       "ونسّق مع فريق التوصيل."},
    },
    "Delivery": {
        "en": {"name": "Delivery",
               "desc": "Get orders to customers: handle products carefully, give accurate "
                       "updates, and coordinate with other teams."},
        "ar": {"name": "التوصيل",
               "desc": "أوصل الطلبات إلى العملاء: تعامل مع المنتجات بعناية، وقدّم معلومات دقيقة، "
                       "ونسّق مع الفرق الأخرى."},
    },
}

SUGGESTIONS = {
    "Days 1-7": {"en": "Ask the assistant about the company, its values and onboarding.",
                 "ar": "اسأل المساعد عن الشركة وقيمها وإجراءات التهيئة."},
    "Day 30": {"en": "Take the knowledge quiz below and complete one practice scenario.",
               "ar": "أدِّ اختبار المعرفة أدناه وأكمل موقفاً تدريبياً واحداً."},
    "Day 60": {"en": "Practise your other scenarios and read the feedback.",
               "ar": "تدرّب على المواقف الأخرى واقرأ الملاحظات."},
    "Day 90": {"en": "Open My progress and download your learning summary for a human review.",
               "ar": "افتح صفحة تقدّمي ونزّل ملخص التعلم لمراجعته مع شخص مسؤول."},
}

EXAMPLES = {
    "en": ["How do I request leave?", "What are the company values?",
           "A customer is angry about a late delivery", "I completed Day 30"],
    "ar": ["كيف أقدم طلب إجازة؟", "ما قيم الشركة؟",
           "العميل غاضب بسبب تأخر التسليم", "أكملت نشاط اليوم 30"],
}
