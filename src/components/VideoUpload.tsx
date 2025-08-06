import React, { useRef, useState } from "react";
import axios from "axios";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Upload, Languages } from "lucide-react";
import { useTranslation } from "./hooks/useTranslation";
import VideoResult from "./VideoResult";

const VideoUpload = () => {
  const { t, languages } = useTranslation();

  const [originalLanguage, setOriginalLanguage] = useState("");
  const [targetLanguage, setTargetLanguage] = useState("");
  const [uploadProgress, setUploadProgress] = useState(0);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [result, setResult] = useState<any>(null);

  const fileInputRef = useRef<HTMLInputElement>(null);

  // Reset for new translation
  const handleNewTranslation = () => {
    setResult(null);
    setSelectedFile(null);
    setOriginalLanguage("");
    setTargetLanguage("");
    setUploadProgress(0);
    if (fileInputRef.current) fileInputRef.current.value = "";
  };

  const handleFileUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    setSelectedFile(file || null);

    if (!file || !originalLanguage || !targetLanguage) {
      alert("Please select a file and both languages.");
      return;
    }

    const formData = new FormData();
    formData.append("file", file);
    formData.append("source_lang", originalLanguage);
    formData.append("target_lang", targetLanguage);

    setUploading(true);
    setUploadProgress(0);

    try {
      const response = await axios.post("http://localhost:8000/analyze", formData, {
        onUploadProgress: (progressEvent) => {
          if (progressEvent.total) {
            const percent = Math.round((progressEvent.loaded * 100) / progressEvent.total);
            setUploadProgress(percent);
          }
        },
      });

      setResult(response.data);
    } catch (error) {
      console.error("Upload failed:", error);
      alert("Upload or analysis failed. Please try again.");
    } finally {
      setUploading(false);
    }
  };

  const handleUploadClick = () => {
    if (!originalLanguage || !targetLanguage) {
      alert("Please select both original and target languages.");
      return;
    }
    fileInputRef.current?.click();
  };

  if (result && result.status === "success") {
    return (
      <VideoResult
        videoUrl={result.video_url}
        subtitleEnUrl={result.original_vtt_url}
        subtitleMnUrl={result.translated_vtt_url}
        onNewTranslation={handleNewTranslation}
      />
    );
  }

  return (
    <div className="max-w-4xl mx-auto space-y-8 px-8 py-12">
      <div className="text-center space-y-6">
        <div className="inline-flex items-center justify-center w-20 h-20 bg-gradient-to-r from-blue-500 to-purple-600 rounded-3xl mb-6">
          <Languages className="w-12 h-12 text-white" />
        </div>
        <h1 className="text-5xl lg:text-6xl font-bold text-foreground">
          {t("translate.title")}
        </h1>
        <p className="text-xl lg:text-2xl text-muted-foreground max-w-3xl mx-auto">
          AI-powered video translation with natural voice cloning
        </p>
      </div>

      <Card className="border-border shadow-xl">
        <CardContent className="p-10 space-y-8">
          {/* Language Selection */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <div className="space-y-3">
              <label className="text-lg font-medium text-foreground">
                {t("translate.originalLanguage")}
              </label>
              <Select value={originalLanguage} onValueChange={setOriginalLanguage}>
                <SelectTrigger className="h-16 text-lg">
                  <SelectValue placeholder="Select language" />
                </SelectTrigger>
                <SelectContent>
                  {languages.map((lang) => (
                    <SelectItem key={lang.code} value={lang.value} className="text-lg py-3">
                      <span className="flex items-center gap-3">
                        <span className="text-xl">{lang.flag}</span>
                        <span>{lang.name}</span>
                      </span>
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-3">
              <label className="text-lg font-medium text-foreground">
                {t("translate.targetLanguage")}
              </label>
              <Select value={targetLanguage} onValueChange={setTargetLanguage}>
                <SelectTrigger className="h-16 text-lg">
                  <SelectValue placeholder="Select language" />
                </SelectTrigger>
                <SelectContent>
                  {languages.map((lang) => (
                    <SelectItem key={lang.code} value={lang.value} className="text-lg py-3">
                      <span className="flex items-center gap-3">
                        <span className="text-xl">{lang.flag}</span>
                        <span>{lang.name}</span>
                      </span>
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>

          {/* Upload Button */}
          <div className="text-center">
            <Button
              variant="default"
              size="lg"
              onClick={handleUploadClick}
              className="w-full sm:w-auto px-12 py-6 text-xl h-16 font-semibold"
              disabled={!originalLanguage || !targetLanguage || uploading}
            >
              <Upload className="w-7 h-7 mr-4" />
              {uploading ? "Uploading..." : t("translate.uploadButton")}
            </Button>
            <input
              ref={fileInputRef}
              type="file"
              accept="video/*"
              onChange={handleFileUpload}
              className="hidden"
            />
          </div>

          {/* Upload Progress */}
          {uploading && (
            <div className="w-full text-center">
              <p className="text-lg text-muted-foreground mb-4">
                Uploading... {uploadProgress}%
              </p>
              <div className="w-full bg-gray-200 rounded-full h-4">
                <div
                  className="bg-blue-500 h-4 rounded-full transition-all duration-300"
                  style={{ width: `${uploadProgress}%` }}
                />
              </div>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
};

export default VideoUpload;