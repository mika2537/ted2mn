import {
  createContext,
  useContext,
  useState,
  useCallback,
  ReactNode,
} from "react";

type Language = {
  code: string;
  name: string;
  flag: string;
  value: string;
  };

// Define the type for translations to improve type safety
interface Translations {
  nav: {
    home: string;
    explore: string;
    pricing: string;
  };
  header: {
    newVideo: string;
  };
  translate: {
    title: string;
    urlPlaceholder: string;
    uploadButton: string;
    originalLanguage: string;
    targetLanguage: string;
    translateButton: string;
    uploading: string;
    uploadingDescription: string;
    uploadingNote: string;
    translating: string;
    translatingDescription: string;
    completed: string;
    completedDescription: string;
    download: string;
    switchAudio: string;
  };
}

const languages: Language[] = [
  { code: "en", name: "English", flag: "🇺🇸" ,value: "English"},
  { code: "mn", name: "Монгол", flag: "🇲🇳", value: "Mongolian" },
  // { code: "ja", name: "日本語", flag: "🇯🇵" },
];

const translations: Record<string, Translations> = {
  en: {
    nav: {
      home: "Home",
      explore: "Explore",
      pricing: "Pricing",
    },
    header: {
      newVideo: "New video",
    },
    translate: {
      title: "Translate your video",
      urlPlaceholder: "Paste video URL",
      uploadButton: "Upload a video",
      originalLanguage: "Original language",
      targetLanguage: "Target language",
      translateButton: "Translate Video",
      uploading: "Uploading...",
      uploadingDescription: "Your video is being uploaded. Please wait.",
      uploadingNote:
        "This may take a few minutes depending on the size of your video.",
      translating: "Translating...",
      translatingDescription: "AI is translating your video content.",
      completed: "Translation Complete!",
      completedDescription: "Your video has been successfully translated.",
      download: "Download",
      switchAudio: "Switch Audio/Subtitles",
    },
  },
  mn: {
    nav: {
      home: "Нүүр",
      explore: "Судлах",
      pricing: "Үнийн санал",
    },
    header: {
      newVideo: "Шинэ видео",
    },
    translate: {
      title: "Видео орчуулах",
      urlPlaceholder: "Видео URL хаягийг наах",
      uploadButton: "Видео оруулах",
      originalLanguage: "Эх хэл",
      targetLanguage: "Орчуулах хэл",
      translateButton: "Видео орчуулах",
      uploading: "Оруулж байна...",
      uploadingDescription: "Таны видео оруулж байна. Түр хүлээнэ үү.",
      uploadingNote: "Видео хэмжээний дагуу хэдэн минут шаардагдах боломжтой.",
      translating: "Орчуулж байна...",
      translatingDescription: "AI таны видео агуулгыг орчуулж байна.",
      completed: "Орчуулга дууссан!",
      completedDescription: "Таны видео амжилттай орчуулагдсан.",
      download: "Татах",
      switchAudio: "Дуу/Дэлгэцийн бичлэг солих",
    },
  },
  ja: {
    nav: {
      home: "ホーム",
      explore: "探検",
      pricing: "価格",
    },
    header: {
      newVideo: "新しい動画",
    },
    translate: {
      title: "動画を翻訳する",
      urlPlaceholder: "動画のURLを貼り付ける",
      uploadButton: "動画をアップロード",
      originalLanguage: "元の言語",
      targetLanguage: "翻訳する言語",
      translateButton: "動画を翻訳",
      uploading: "アップロード中...",
      uploadingDescription:
        "動画をアップロードしています。しばらくお待ちください。",
      uploadingNote: "動画のサイズによっては数分かかる場合があります。",
      translating: "翻訳中...",
      translatingDescription: "AIが動画の内容を翻訳しています。",
      completed: "翻訳完了！",
      completedDescription: "動画の翻訳が成功しました。",
      download: "ダウンロード",
      switchAudio: "音声/字幕を切り替える",
    },
  },
};

// Define the context type
interface TranslationContextType {
  t: (key: string) => string;
  currentLanguage: string;
  setLanguage: (lang: string) => void;
  languages: Language[];
}

const TranslationContext = createContext<TranslationContextType | null>(null);


export const useTranslation = () => {
  const [currentLanguage, setCurrentLanguage] = useState<string>('en');

  const setLanguage = useCallback((lang: string) => {
    setCurrentLanguage(lang);
  }, []);

  const t = useCallback((key: string) => {
    const keys = key.split('.');
    let translation: any = translations[currentLanguage as keyof typeof translations];
    
    for (const k of keys) {
      translation = translation?.[k];
    }
    
    return translation || key;
  }, [currentLanguage]);

  return {
    t,
    currentLanguage,
    setLanguage,
    languages,
  };
};
