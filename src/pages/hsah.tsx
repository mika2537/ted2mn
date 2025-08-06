'use client';

import React, { useEffect, useRef, useState } from 'react';

// import { useTranslation } from "@/components/hooks/useTranslation"; // Adjusted path
// import VideoTranslator from "@/pages/VideoTranslator";

const Index = () => {
  // const { t } = useTranslation();

  const videoRef = useRef<HTMLVideoElement>(null);

  const [activeSubtitle, setActiveSubtitle] = useState("mn");

    useEffect(() => {
      const video = videoRef.current;
      if (!video) return;
    
      const tracks = video.textTracks;
      for (let i = 0; i < tracks.length; i++) {
        if (activeSubtitle === "off") {
          tracks[i].mode = "disabled";
        } else if (tracks[i].language === activeSubtitle) {
          console.log('psda');
          tracks[i].mode = "showing";
        } else {
          tracks[i].mode = "disabled";
        }
      }
    }, [activeSubtitle]);

  return (
    <video controls width="840" height="460" ref={videoRef}>
  <source
    src="/static/5ca0f628-073e-477b-beb5-00ba07f3ca67_subtitled.mp4"
    type="video/mp4"
  />
  <track
    src="/static/5ca0f628-073e-477b-beb5-00ba07f3ca67_translated.vtt"
    kind="subtitles"
    srcLang="en"
    label="English"
  />
  <track
    src="/static/5ca0f628-073e-477b-beb5-00ba07f3ca67_translated.vtt"
    kind="subtitles"
    srcLang="mn"
    label="Монгол"
    default
  />
</video>
  );
};

export default Index;