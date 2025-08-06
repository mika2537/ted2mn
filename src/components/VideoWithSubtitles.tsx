import React from 'react';
import { Button } from '@/components/ui/button'; // optional, use plain button if needed

const VideoWithSubtitles = () => {
  const downloadVideo = () => {
    // Optional: call your backend route if subtitle-burned video is available
    window.location.href = '/videos/video.mp4';
  };

  return (
    <div className="p-6 space-y-4 max-w-3xl mx-auto">
      <h2 className="text-xl font-bold">Video with Subtitles</h2>

      <video width="100%" height="auto" controls>
        <source src="/videos/ted_video_en.mp4" type="video/mp4" />
        <track
          src="/subs/ted_video.en.vtt"
          kind="subtitles"
          srcLang="en"
          label="English"
        />
        Your browser does not support the video tag.
      </video>

      <Button onClick={downloadVideo}>Download Video</Button>
      {/* Or use: <button onClick={downloadVideo}>Download Video</button> */}
    </div>
  );
};

export default VideoWithSubtitles;