import { Progress } from '@/components/ui/progress';
import { Card, CardContent } from '@/components/ui/card';
import { Upload, Sparkles, CheckCircle } from 'lucide-react';
import { useTranslation } from './hooks/useTranslation';

interface VideoProgressProps {
  stage: 'uploading' | 'translating' | 'completed';
  progress: number;
}

const VideoProgress = ({ stage, progress }: VideoProgressProps) => {
  const { t } = useTranslation();

  const getStageIcon = () => {
    switch (stage) {
      case 'uploading':
        return <Upload className="w-8 h-8 text-primary animate-pulse" />;
      case 'translating':
        return <Sparkles className="w-8 h-8 text-primary animate-pulse" />;
      case 'completed':
        return <CheckCircle className="w-8 h-8 text-green-500" />;
    }
  };

  const getStageTitle = () => {
    switch (stage) {
      case 'uploading':
        return t('translate.uploading');
      case 'translating':
        return t('translate.translating');
      case 'completed':
        return t('translate.completed');
    }
  };

  const getStageDescription = () => {
    switch (stage) {
      case 'uploading':
        return t('translate.uploadingDescription');
      case 'translating':
        return t('translate.translatingDescription');
      case 'completed':
        return t('translate.completedDescription');
    }
  };

  return (
    <div className="max-w-2xl mx-auto">
      <Card className="border-border shadow-lg">
        <CardContent className="p-8 text-center space-y-6">
          <div className="flex justify-center">
            {getStageIcon()}
          </div>
          
          <div className="space-y-2">
            <h2 className="text-2xl font-bold text-foreground">
              {getStageTitle()}
            </h2>
            <p className="text-muted-foreground">
              {getStageDescription()}
            </p>
          </div>

          {stage !== 'completed' && (
            <>
              <Progress value={progress} className="w-full h-2" />
              <p className="text-sm text-muted-foreground">
                {stage === 'uploading' && t('translate.uploadingNote')}
              </p>
            </>
          )}
        </CardContent>
      </Card>
    </div>
  );
};

export default VideoProgress;