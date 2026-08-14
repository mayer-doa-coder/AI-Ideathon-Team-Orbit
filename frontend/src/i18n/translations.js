// Full English/Bangla dictionary for the AgriSense AI frontend. Organized
// by component/page so a translator (or future editor) can find a string
// the same way they'd find its JSX. Dynamic values (crop names, farmer
// text, LLM/server output) are never translated here — only static UI
// chrome — see context/LanguageContext.jsx for the lookup helpers, and
// data/useHomeContent.js for the marketing-copy twin-file approach used for
// the large homeContent.js dataset instead of key-by-key entries here.
export const translations = {
  en: {
    common: {
      genericError: "Something went wrong. Please try again.",
    },
    chatHeader: {
      brand: "AgriSense AI",
      subtitle: "Crop Doctor Assistant",
      online: "Online",
      logout: "Log out",
      languageToggleLabel: "বাং",
      languageToggleTitle: "বাংলায় দেখুন",
    },
    chatInput: {
      defaultPlaceholder: "Ask about your crop...",
      photoNotePlaceholder: "Add a note about the photo (optional)...",
      imageTypeError: "Please choose an image file.",
      imageSizeError: "That photo is too large — please use one under 8MB.",
      imageDropError: "Please drop an image file.",
      voiceUnavailableAria: "Voice input (temporarily unavailable)",
      voiceUnavailableTitle: "Voice input is temporarily unavailable",
      attachPhotoLabel: "Attach a crop photo for disease detection",
      removePhotoLabel: "Remove photo",
      sendLabel: "Send message",
      photoPreviewAlt: "Selected crop photo",
      imageDefaultCaption: "Here's a photo of my crop — what's wrong with it?",
      locationGranted: 'Using your current location for "near me" searches',
      locationDenied: 'Location access denied — enable it in your browser to use "near me" searches',
      locationIdle: "Share your location so I can find suppliers near you",
      recordingStatus: "Recording... tap the mic again to stop and send",
      processingVoice: "Processing your voice message...",
      voiceUnsupported: "Voice recording isn't supported in this browser.",
      micDenied: "Microphone access was denied — enable it in your browser to use voice input.",
      voiceProcessError: "Couldn't process that recording — please try again.",
      voicePlaceholderText: "🎤 Voice message",
    },
    chatMessage: {
      voiceTag: "Voice message",
      photoAlt: "Attached crop photo",
      transcriptFailedNote: "Couldn't make out the words — see reply below",
    },
    voiceProcessing: {
      thinking: "Thinking...",
      listening: "Listening...",
    },
    farmProfileStrip: {
      location: "Location",
      acreage: "Land",
      soilType: "Soil",
      water: "Water",
      budget: "Budget",
      season: "Season",
      pending: "pending",
      acresValueTemplate: "{acres} acres",
    },
    traceLog: {
      title: "Live Agent Trace",
      callsSuffix: "calls",
      empty: "Tool calls will appear here in real time as the agent works.",
    },
    traceEntry: {
      voiceInput: "Voice input",
      voiceOutput: "Voice output",
      paramsSent: "Parameters sent",
      rawResponse: "Raw response",
      summaryPrefix: "→",
    },
    weatherWidget: {
      title: "Weather",
      empty: "Weather forecast will appear here once the agent checks it.",
      headingTemplate: "{location} — Next {days} Days",
      live: "LIVE",
      liveTitle: "Backed by a real Open-Meteo forecast call",
      rainfallTemplate: "Rainfall: {days}-day forecast",
      tempTemplate: "Temp: {range}°C",
      barTitleTemplate: "{date}: {mm}mm",
    },
    marketPriceCard: {
      title: "Market Price Intelligence",
      loading: "Loading market data...",
      historicalAvg: "Historical avg",
      change7d: "7-day change",
      change30d: "30-day change",
      insufficientData: "insufficient data",
      why: "Why?",
      sourceTemplate: "Source: {source}",
      metaTemplate: "{district} · as of {date}",
      metaSeasonSuffix: " · {season} season",
      national: "National",
      sellNow: "SELL NOW",
      store: "STORE",
      wait: "WAIT",
      barTitleTemplate: "{date}: ৳{price}/{unit}",
    },
    cropComparison: {
      title: "Recommended Crops",
      subtitle: "Based on your farm profile",
    },
    cropCard: {
      suitability: "Suitability",
      water: "Water",
      risk: "Risk",
      profit: "Profit",
      why: "Why?",
      selected: "Selected",
      select: "Select",
    },
    seasonPlanTimeline: {
      title: "Season Plan",
      subtitleTemplate: "{cropName} · click a milestone for details",
      dotAriaTemplate: "{name} — {date}",
      dotTitleTemplate: "{from} → {date}",
    },
    milestoneDetail: {
      titleTemplate: "{name} — {date}",
      movedTemplate: "Moved from {from} to {to} — {reason}",
      what: "What",
      whyThisDate: "Why this date",
      quantity: "Quantity",
      cost: "Cost",
      organicAlternative: "Organic alternative",
    },
    financialBreakdown: {
      title: "Financial Breakdown",
      totalCost: "Total Cost",
      revenue: "Revenue",
      netProfit: "Net Profit",
      roi: "ROI",
      breakEven: "Break-even",
      breakEvenTemplate: "{tons} tons",
      helpNote:
        'Ask in the chat — e.g. "what if my budget drops 40%?" — and the agent will recalculate this against your actual plan.',
    },
    alertsFeed: {
      title: "Alerts",
      live: "LIVE",
      liveTitle: "Backed by the real monitor graph",
      simulate: "Simulate next check",
      checking: "Checking...",
      liveCaption: "Real monitor sweep, injected forecast — clearly test data, not a live weather event.",
      idleCaption: "The agent checks your plan periodically — even when you're not looking.",
      empty: "No checks yet.",
      entryTemplate: "{date} — {text}",
    },
    knowledgeSources: {
      groundedIn: "Grounded in:",
    },
    chatPage: {
      inputPlaceholder: "Tell me about your farm, ask a question, or try a what-if...",
      loadingProfile: "Loading your farm profile...",
      loadErrorTemplate: "Couldn't load your conversation: {error}",
      errorTemplate: "Something went wrong: {error}",
      monitorCheckFailedTemplate: "Monitor check failed: {error}",
      monitorCheckCompleteNoChange: "Monitor check complete — no adjustment needed this time.",
      monitorCheckCompleteTemplate: "Monitor check complete — {reason}",
      illGoWithTemplate: "I'll go with {crop}.",
      heavyRainAlertTemplate: "Heavy rain ({mm}mm) forecast on {date}.",
      greeting:
        "Hi, I'm your AgriSense AI planning assistant. Tell me about your farm — location, " +
        "acreage, soil type, water availability, budget, and the season you're planning for — " +
        "and I'll check the weather and knowledge base to build you a season plan.",
    },
    loginPage: {
      brand: "AgriSense AI",
      welcomeBack: "Welcome back",
      createAccount: "Create your account",
      loginSubtitle: "Log in to continue your farm planning session.",
      registerSubtitle: "Register to start a new farm planning session.",
      username: "Username",
      password: "Password",
      pleaseWait: "Please wait...",
      logIn: "Log In",
      createAccountButton: "Create Account",
      toggleToRegister: "Don't have an account? Register",
      toggleToLogin: "Already have an account? Log in",
    },
    askPage: {
      title: "Ask AgriSense",
      subtitle: "Ask a question in plain language — it's answered from the embedded BARC handbook only.",
      placeholder: "e.g. when should I plant Boro rice and how much urea does it need?",
      thinking: "Thinking...",
      ask: "Ask",
      sourcesTemplate: "Sources ({count})",
      similarityTemplate: "similarity {value}",
      cropTemplate: "crop: {value}",
      topicTemplate: "topic: {value}",
      pageTemplate: "page {value}",
    },
    ragTestPage: {
      title: "Knowledge Base Retriever",
      subtitle: "Query the embedded BARC handbook and inspect the raw chunks the retriever returns.",
      placeholder: "e.g. how to control brown planthopper in rice",
      cropFilterPlaceholder: "crop filter (optional)",
      topicFilterPlaceholder: "topic filter (optional)",
      searching: "Searching...",
      search: "Search",
      countTemplate: "{count} chunk(s) returned",
      similarityTemplate: "similarity {value}",
      cropTemplate: "crop: {value}",
      topicTemplate: "topic: {value}",
      pageTemplate: "page {value}",
    },
    home: {
      siteHeader: {
        navHome: "Home",
        navAbout: "About",
        navServices: "Services",
        navContact: "Contact",
        brand: "AgriSense AI",
        cropDoctor: "Crop Doctor",
        askCropDoctor: "Ask Crop Doctor",
        toggleMenu: "Toggle menu",
      },
      hero: {
        tryCropDoctor: "Try Crop Doctor",
        seeHowItWorks: "See How It Works",
        whatMakesUsDifferent: "What Makes Us Different",
      },
      about: {
        subTitle: "About Us",
        watchDemo: "Watch demo",
      },
      whyChooseUs: {
        exploreServices: "Explore Our Services",
        callUs: "Call us:",
      },
      services: {
        subTitle: "our services",
        heading1: "AI-Powered",
        heading2: "Farm Services",
        viewAll: "view all services",
      },
      faq: {
        subTitle: "Ask, Learn, and Grow With Us",
        heading: "Ask About AgriSense AI, Learn Smarter Farming",
      },
      testimonials: {
        subTitle: "our Testimonials",
        heading1: "Farmers Talk About",
        heading2: "AgriSense AI",
      },
      newsBlog: {
        subTitle: "our latest news and insights",
        heading: "AgriSense AI News & Blog",
      },
      footer: {
        callForDetails: "call for details",
        emailUs: "email us",
        newsletterHeading: "Get farming insights from AgriSense AI",
        emailPlaceholder: "Enter your email",
        subscribe: "subscribe now",
        services: "Services",
        resources: "Resources",
        company: "Company",
        copyright: "© 2026 AgriSense AI. All Rights Reserved.",
      },
      carousel: {
        previous: "Previous",
        next: "Next",
      },
    },
    errors: {
      genericFallback: "Something went wrong. Please try again.",
      sessionExpired: "Session expired",
      photoReadError: "Couldn't read the selected photo.",
      streamingUnsupported: "Streaming is not supported in this browser.",
    },
  },

  bn: {
    common: {
      genericError: "কিছু একটা সমস্যা হয়েছে। আবার চেষ্টা করুন।",
    },
    chatHeader: {
      brand: "AgriSense AI",
      subtitle: "ক্রপ ডক্টর সহকারী",
      online: "অনলাইন",
      logout: "লগ আউট",
      languageToggleLabel: "EN",
      languageToggleTitle: "View in English",
    },
    chatInput: {
      defaultPlaceholder: "আপনার ফসল সম্পর্কে জিজ্ঞাসা করুন...",
      photoNotePlaceholder: "ছবি সম্পর্কে একটি নোট যোগ করুন (ঐচ্ছিক)...",
      imageTypeError: "অনুগ্রহ করে একটি ছবি ফাইল নির্বাচন করুন।",
      imageSizeError: "ছবিটি অনেক বড় — অনুগ্রহ করে ৮MB এর কম আকারের ছবি ব্যবহার করুন।",
      imageDropError: "অনুগ্রহ করে একটি ছবি ফাইল ড্রপ করুন।",
      voiceUnavailableAria: "ভয়েস ইনপুট (সাময়িকভাবে অনুপলব্ধ)",
      voiceUnavailableTitle: "ভয়েস ইনপুট সাময়িকভাবে অনুপলব্ধ",
      attachPhotoLabel: "রোগ শনাক্তকরণের জন্য ফসলের ছবি সংযুক্ত করুন",
      removePhotoLabel: "ছবি সরান",
      sendLabel: "বার্তা পাঠান",
      photoPreviewAlt: "নির্বাচিত ফসলের ছবি",
      imageDefaultCaption: "এই আমার ফসলের একটি ছবি — এতে কী সমস্যা হয়েছে?",
      locationGranted: '"আশেপাশে" খোঁজার জন্য আপনার বর্তমান অবস্থান ব্যবহার করা হচ্ছে',
      locationDenied: 'অবস্থান অ্যাক্সেস প্রত্যাখ্যাত — "আশেপাশে" খোঁজার জন্য আপনার ব্রাউজারে এটি চালু করুন',
      locationIdle: "আপনার কাছাকাছি সরবরাহকারী খুঁজে পেতে আপনার অবস্থান শেয়ার করুন",
      recordingStatus: "রেকর্ড হচ্ছে... থামিয়ে পাঠাতে মাইকে আবার চাপুন",
      processingVoice: "আপনার ভয়েস বার্তা প্রক্রিয়া করা হচ্ছে...",
      voiceUnsupported: "এই ব্রাউজারে ভয়েস রেকর্ডিং সমর্থিত নয়।",
      micDenied: "মাইক্রোফোন অ্যাক্সেস প্রত্যাখ্যাত হয়েছে — ভয়েস ইনপুট ব্যবহার করতে ব্রাউজারে অনুমতি দিন।",
      voiceProcessError: "রেকর্ডিং প্রক্রিয়া করা যায়নি — অনুগ্রহ করে আবার চেষ্টা করুন।",
      voicePlaceholderText: "🎤 ভয়েস বার্তা",
    },
    chatMessage: {
      voiceTag: "ভয়েস বার্তা",
      photoAlt: "সংযুক্ত ফসলের ছবি",
      transcriptFailedNote: "কথাগুলো বোঝা যায়নি — নিচের উত্তর দেখুন",
    },
    voiceProcessing: {
      thinking: "চিন্তা করছে...",
      listening: "শুনছে...",
    },
    farmProfileStrip: {
      location: "অবস্থান",
      acreage: "জমি",
      soilType: "মাটি",
      water: "পানি",
      budget: "বাজেট",
      season: "মৌসুম",
      pending: "অপেক্ষমাণ",
      acresValueTemplate: "{acres} একর",
    },
    traceLog: {
      title: "লাইভ এজেন্ট ট্রেস",
      callsSuffix: "টি কল",
      empty: "এজেন্ট কাজ করার সাথে সাথে টুল কলগুলো এখানে রিয়েল-টাইমে দেখা যাবে।",
    },
    traceEntry: {
      voiceInput: "ভয়েস ইনপুট",
      voiceOutput: "ভয়েস আউটপুট",
      paramsSent: "প্রেরিত প্যারামিটার",
      rawResponse: "মূল প্রতিক্রিয়া",
      summaryPrefix: "→",
    },
    weatherWidget: {
      title: "আবহাওয়া",
      empty: "এজেন্ট আবহাওয়া পরীক্ষা করার পর পূর্বাভাস এখানে দেখা যাবে।",
      headingTemplate: "{location} — আগামী {days} দিন",
      live: "লাইভ",
      liveTitle: "সরাসরি Open-Meteo পূর্বাভাস কলের উপর ভিত্তি করে",
      rainfallTemplate: "বৃষ্টিপাত: {days}-দিনের পূর্বাভাস",
      tempTemplate: "তাপমাত্রা: {range}°সে",
      barTitleTemplate: "{date}: {mm}মিমি",
    },
    marketPriceCard: {
      title: "বাজার মূল্য বিশ্লেষণ",
      loading: "বাজারের তথ্য লোড হচ্ছে...",
      historicalAvg: "গড় মূল্য (ঐতিহাসিক)",
      change7d: "৭-দিনের পরিবর্তন",
      change30d: "৩০-দিনের পরিবর্তন",
      insufficientData: "পর্যাপ্ত তথ্য নেই",
      why: "কেন?",
      sourceTemplate: "উৎস: {source}",
      metaTemplate: "{district} · হালনাগাদ {date}",
      metaSeasonSuffix: " · {season} মৌসুম",
      national: "জাতীয়",
      sellNow: "এখনই বিক্রি করুন",
      store: "মজুদ রাখুন",
      wait: "অপেক্ষা করুন",
      barTitleTemplate: "{date}: ৳{price}/{unit}",
    },
    cropComparison: {
      title: "প্রস্তাবিত ফসল",
      subtitle: "আপনার খামারের তথ্যের ভিত্তিতে",
    },
    cropCard: {
      suitability: "উপযুক্ততা",
      water: "পানি",
      risk: "ঝুঁকি",
      profit: "লাভ",
      why: "কেন?",
      selected: "নির্বাচিত",
      select: "নির্বাচন করুন",
    },
    seasonPlanTimeline: {
      title: "মৌসুম পরিকল্পনা",
      subtitleTemplate: "{cropName} · বিস্তারিত জানতে একটি ধাপে ক্লিক করুন",
      dotAriaTemplate: "{name} — {date}",
      dotTitleTemplate: "{from} → {date}",
    },
    milestoneDetail: {
      titleTemplate: "{name} — {date}",
      movedTemplate: "{from} থেকে সরিয়ে {to} করা হয়েছে — {reason}",
      what: "কী করতে হবে",
      whyThisDate: "কেন এই তারিখ",
      quantity: "পরিমাণ",
      cost: "খরচ",
      organicAlternative: "জৈব বিকল্প",
    },
    financialBreakdown: {
      title: "আর্থিক বিবরণ",
      totalCost: "মোট খরচ",
      revenue: "আয়",
      netProfit: "নিট লাভ",
      roi: "বিনিয়োগে মুনাফা (ROI)",
      breakEven: "ব্রেক-ইভেন",
      breakEvenTemplate: "{tons} টন",
      helpNote:
        'চ্যাটে জিজ্ঞাসা করুন — যেমন "আমার বাজেট ৪০% কমে গেলে কী হবে?" — এজেন্ট আপনার প্রকৃত পরিকল্পনার ভিত্তিতে এটি আবার হিসাব করে দেবে।',
    },
    alertsFeed: {
      title: "সতর্কতা",
      live: "লাইভ",
      liveTitle: "সরাসরি মনিটর গ্রাফের উপর ভিত্তি করে",
      simulate: "পরবর্তী পরীক্ষা সিমুলেট করুন",
      checking: "পরীক্ষা চলছে...",
      liveCaption: "প্রকৃত মনিটর স্ক্যান, ইনজেক্টেড পূর্বাভাস — স্পষ্টভাবে টেস্ট ডেটা, লাইভ আবহাওয়া ঘটনা নয়।",
      idleCaption: "আপনি না দেখলেও এজেন্ট নিয়মিত বিরতিতে আপনার পরিকল্পনা যাচাই করে।",
      empty: "এখনো কোনো পরীক্ষা হয়নি।",
      entryTemplate: "{date} — {text}",
    },
    knowledgeSources: {
      groundedIn: "তথ্যসূত্র:",
    },
    chatPage: {
      inputPlaceholder: "আপনার খামার সম্পর্কে বলুন, প্রশ্ন করুন, অথবা একটি হোয়াট-ইফ চেষ্টা করুন...",
      loadingProfile: "আপনার খামারের তথ্য লোড হচ্ছে...",
      loadErrorTemplate: "আপনার কথোপকথন লোড করা যায়নি: {error}",
      errorTemplate: "কিছু একটা সমস্যা হয়েছে: {error}",
      monitorCheckFailedTemplate: "মনিটর পরীক্ষা ব্যর্থ হয়েছে: {error}",
      monitorCheckCompleteNoChange: "মনিটর পরীক্ষা সম্পন্ন — এই মুহূর্তে কোনো পরিবর্তনের প্রয়োজন নেই।",
      monitorCheckCompleteTemplate: "মনিটর পরীক্ষা সম্পন্ন — {reason}",
      illGoWithTemplate: "আমি {crop} বেছে নিচ্ছি।",
      heavyRainAlertTemplate: "{date} তারিখে ভারী বৃষ্টির (~{mm}মিমি) পূর্বাভাস রয়েছে।",
      greeting:
        "হ্যালো, আমি আপনার AgriSense AI পরিকল্পনা সহকারী। আপনার খামার সম্পর্কে বলুন — অবস্থান, " +
        "জমির পরিমাণ, মাটির ধরন, পানির প্রাপ্যতা, বাজেট এবং যে মৌসুমের জন্য পরিকল্পনা করছেন — " +
        "আমি আবহাওয়া ও জ্ঞানভাণ্ডার যাচাই করে আপনার জন্য একটি মৌসুম পরিকল্পনা তৈরি করে দেব।",
    },
    loginPage: {
      brand: "AgriSense AI",
      welcomeBack: "আবার স্বাগতম",
      createAccount: "আপনার অ্যাকাউন্ট তৈরি করুন",
      loginSubtitle: "আপনার খামার পরিকল্পনা সেশন চালিয়ে যেতে লগ ইন করুন।",
      registerSubtitle: "নতুন খামার পরিকল্পনা সেশন শুরু করতে নিবন্ধন করুন।",
      username: "ইউজারনেম",
      password: "পাসওয়ার্ড",
      pleaseWait: "অনুগ্রহ করে অপেক্ষা করুন...",
      logIn: "লগ ইন করুন",
      createAccountButton: "অ্যাকাউন্ট তৈরি করুন",
      toggleToRegister: "কোনো অ্যাকাউন্ট নেই? নিবন্ধন করুন",
      toggleToLogin: "ইতিমধ্যে অ্যাকাউন্ট আছে? লগ ইন করুন",
    },
    askPage: {
      title: "AgriSense-কে জিজ্ঞাসা করুন",
      subtitle: "সহজ ভাষায় প্রশ্ন করুন — শুধুমাত্র এম্বেডেড BARC হ্যান্ডবুক থেকে উত্তর দেওয়া হয়।",
      placeholder: "যেমন: বোরো ধান কখন লাগানো উচিত এবং কতটা ইউরিয়া দরকার?",
      thinking: "চিন্তা করছে...",
      ask: "জিজ্ঞাসা করুন",
      sourcesTemplate: "তথ্যসূত্র ({count})",
      similarityTemplate: "মিল {value}",
      cropTemplate: "ফসল: {value}",
      topicTemplate: "বিষয়: {value}",
      pageTemplate: "পৃষ্ঠা {value}",
    },
    ragTestPage: {
      title: "জ্ঞানভাণ্ডার অনুসন্ধান",
      subtitle: "এম্বেডেড BARC হ্যান্ডবুক অনুসন্ধান করুন এবং রিট্রিভার যে কাঁচা অংশগুলো ফেরত দেয় তা দেখুন।",
      placeholder: "যেমন: ধানে বাদামি গাছফড়িং নিয়ন্ত্রণ কীভাবে করবেন",
      cropFilterPlaceholder: "ফসল ফিল্টার (ঐচ্ছিক)",
      topicFilterPlaceholder: "বিষয় ফিল্টার (ঐচ্ছিক)",
      searching: "খোঁজা হচ্ছে...",
      search: "খুঁজুন",
      countTemplate: "{count}টি অংশ পাওয়া গেছে",
      similarityTemplate: "মিল {value}",
      cropTemplate: "ফসল: {value}",
      topicTemplate: "বিষয়: {value}",
      pageTemplate: "পৃষ্ঠা {value}",
    },
    home: {
      siteHeader: {
        navHome: "হোম",
        navAbout: "আমাদের সম্পর্কে",
        navServices: "সেবাসমূহ",
        navContact: "যোগাযোগ",
        brand: "AgriSense AI",
        cropDoctor: "ক্রপ ডক্টর",
        askCropDoctor: "ক্রপ ডক্টরকে জিজ্ঞাসা করুন",
        toggleMenu: "মেনু টগল করুন",
      },
      hero: {
        tryCropDoctor: "ক্রপ ডক্টর ব্যবহার করুন",
        seeHowItWorks: "কীভাবে কাজ করে দেখুন",
        whatMakesUsDifferent: "আমাদের বিশেষত্ব",
      },
      about: {
        subTitle: "আমাদের সম্পর্কে",
        watchDemo: "ডেমো দেখুন",
      },
      whyChooseUs: {
        exploreServices: "আমাদের সেবাসমূহ দেখুন",
        callUs: "আমাদের কল করুন:",
      },
      services: {
        subTitle: "আমাদের সেবাসমূহ",
        heading1: "এআই-চালিত",
        heading2: "কৃষি সেবা",
        viewAll: "সব সেবা দেখুন",
      },
      faq: {
        subTitle: "জিজ্ঞাসা করুন, শিখুন, আমাদের সাথে বেড়ে উঠুন",
        heading: "AgriSense AI সম্পর্কে জিজ্ঞাসা করুন, স্মার্ট কৃষি শিখুন",
      },
      testimonials: {
        subTitle: "আমাদের কৃষকদের মতামত",
        heading1: "কৃষকরা যা বলছেন",
        heading2: "AgriSense AI সম্পর্কে",
      },
      newsBlog: {
        subTitle: "আমাদের সাম্প্রতিক খবর ও তথ্য",
        heading: "AgriSense AI খবর ও ব্লগ",
      },
      footer: {
        callForDetails: "বিস্তারিত জানতে কল করুন",
        emailUs: "ইমেইল করুন",
        newsletterHeading: "AgriSense AI থেকে কৃষি বিষয়ক তথ্য পান",
        emailPlaceholder: "আপনার ইমেইল দিন",
        subscribe: "সাবস্ক্রাইব করুন",
        services: "সেবাসমূহ",
        resources: "রিসোর্স",
        company: "কোম্পানি",
        copyright: "© ২০২৬ AgriSense AI। সর্বস্বত্ব সংরক্ষিত।",
      },
      carousel: {
        previous: "পূর্ববর্তী",
        next: "পরবর্তী",
      },
    },
    errors: {
      genericFallback: "কিছু একটা সমস্যা হয়েছে। আবার চেষ্টা করুন।",
      sessionExpired: "সেশনের মেয়াদ শেষ হয়ে গেছে",
      photoReadError: "নির্বাচিত ছবিটি পড়া যায়নি।",
      streamingUnsupported: "এই ব্রাউজারে স্ট্রিমিং সমর্থিত নয়।",
    },
  },
};

const LANGUAGE_STORAGE_KEY = "agrisense_language";

// Plain (non-hook) helpers — used by services/*.js, which are outside the
// React tree and can't call useLanguage(). LanguageContext.jsx wraps these
// same functions for components.
export function getStoredLanguage() {
  if (typeof window === "undefined") return "en";
  return localStorage.getItem(LANGUAGE_STORAGE_KEY) === "bn" ? "bn" : "en";
}

export function setStoredLanguage(language) {
  localStorage.setItem(LANGUAGE_STORAGE_KEY, language === "bn" ? "bn" : "en");
}

function lookup(dict, key) {
  return key.split(".").reduce((acc, part) => (acc == null ? acc : acc[part]), dict);
}

// Dotted-path lookup (e.g. "chatHeader.online") — falls back to English,
// then to the key itself, so a missing/typo'd key never renders blank.
export function translate(key, language = getStoredLanguage()) {
  const fromLang = lookup(translations[language], key);
  if (fromLang !== undefined) return fromLang;
  const fromEnglish = lookup(translations.en, key);
  return fromEnglish !== undefined ? fromEnglish : key;
}

// Template substitution for strings with dynamic values, e.g.
// tf("weatherWidget.headingTemplate", { location: "Rajshahi", days: 7 })
// — kept separate from translate() rather than prefix/suffix concatenation
// so each language can reorder words around the placeholders correctly.
export function tf(key, vars, language = getStoredLanguage()) {
  const template = translate(key, language);
  return Object.entries(vars).reduce(
    (str, [k, v]) => str.replaceAll(`{${k}}`, v ?? ""),
    template
  );
}

export { LANGUAGE_STORAGE_KEY };
