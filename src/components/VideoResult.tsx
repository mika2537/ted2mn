import React, { useRef, useState, useEffect } from "react";

interface VideoResultProps {
  videoUrl: string;
  subtitleEnUrl: string;
  subtitleMnUrl: string;
  onNewTranslation: () => void;
}

const VideoResult: React.FC<VideoResultProps> = ({
  videoUrl,
  subtitleEnUrl,
  subtitleMnUrl,
  onNewTranslation,
}) => {
  const videoRef = useRef<HTMLVideoElement>(null);
  const menuRef = useRef<HTMLDivElement>(null);
  const [showMenu, setShowMenu] = useState(false);
  const [activeSubtitle, setActiveSubtitle] = useState<"en" | "mn" | "off">("en");

  const switchSubtitle = (lang: "en" | "mn" | "off") => {
    setActiveSubtitle(lang);
    setShowMenu(false);
  };

  const downloadVideo = () => {
    const link = document.createElement("a");
    link.href = videoUrl;
    link.download = "translated_video.mp4";
    link.click();
  };

  // Close menu when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(event.target as Node)) {
        setShowMenu(false);
      }
    };
    if (showMenu) {
      window.addEventListener("click", handleClickOutside);
    }
    return () => window.removeEventListener("click", handleClickOutside);
  }, [showMenu]);

  useEffect(() => {
    console.log('activeSubtitle', activeSubtitle);
    const video = videoRef.current;
    if (!video) return;
  
    const tracks = video.textTracks;
    console.log('tracks', tracks);
    for (let i = 0; i < tracks.length; i++) {
      if (activeSubtitle === "off") {
        tracks[i].mode = "disabled";
      } else if (tracks[i].language === activeSubtitle) {
        tracks[i].mode = "showing";
      } else {
        tracks[i].mode = "disabled";
      }
    }
  }, [activeSubtitle]);

  return (
    <div className="max-w-6xl mx-auto space-y-8 px-8 py-12">
      <h2 className="text-4xl lg:text-5xl font-bold text-center mb-8">Translated Video</h2>

      <div className="relative bg-black rounded-2xl overflow-hidden shadow-2xl">
        <video
          controls
          ref={videoRef}
          className="w-full h-auto min-h-[50vh] max-h-[80vh] object-contain"
          style={{ aspectRatio: '16/9' }}
        >
          <source src={videoUrl} type="video/mp4" />
          {activeSubtitle === "en" && (
            <track
              key="en"
              src={subtitleEnUrl}
              kind="subtitles"
              srcLang="en"
              label="English"
            />
          )}
          {activeSubtitle === "mn" && (
            <track
              key="mn"
              src={subtitleMnUrl}
              kind="subtitles"
              srcLang="mn"
              label="Монгол"
            />
          )}
        </video>

        {/* Subtitle settings button */}
        <div className="absolute top-6 right-6 z-10" ref={menuRef}>
          <button
            onClick={() => setShowMenu((prev) => !prev)}
            className="w-12 h-12 flex items-center justify-center text-white bg-black/60 rounded-full hover:bg-black/80 transition-colors text-lg"
            aria-label="Subtitle Settings"
          >
            ⚙️
          </button>

          {showMenu && (
            <div className="mt-3 absolute right-0 bg-black/95 text-white text-base rounded-xl shadow-2xl w-56 py-2">
              <button
                onClick={() => switchSubtitle("en")}
                className={`block px-5 py-3 hover:bg-white/10 w-full text-left text-base ${
                  activeSubtitle === "en" ? "bg-white/20" : ""
                }`}
              >
                English Subtitles
              </button>
              <button
                onClick={() => switchSubtitle("mn")}
                className={`block px-5 py-3 hover:bg-white/10 w-full text-left text-base ${
                  activeSubtitle === "mn" ? "bg-white/20" : ""
                }`}
              >
                Монгол хадмал
              </button>
              <button
                onClick={() => switchSubtitle("off")}
                className={`block px-5 py-3 hover:bg-white/10 w-full text-left text-base ${
                  activeSubtitle === "off" ? "bg-white/20" : ""
                }`}
              >
                Turn Off Subtitles
              </button>
            </div>
          )}
        </div>
      </div>

      <div className="flex flex-col sm:flex-row gap-6">
        <button
          onClick={downloadVideo}
          className="flex-1 py-4 px-8 bg-gray-800 text-white text-lg rounded-xl hover:bg-gray-700 transition-colors font-semibold"
        >
          Download Video
        </button>
        <button
          onClick={onNewTranslation}
          className="flex-1 py-4 px-8 border-2 border-gray-300 text-gray-700 text-lg rounded-xl hover:bg-gray-50 transition-colors font-semibold"
        >
          Translate Another Video
        </button>
      </div>
    </div>
  );
};

export default VideoResult;