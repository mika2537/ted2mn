
import { useTranslation } from "@/components/hooks/useTranslation"; // Adjusted path
import VideoTranslator from "@/pages/VideoTranslator";

const Index = () => {
  const { t } = useTranslation();

  return (
    <div>
      <VideoTranslator />
    </div>
  );
};

export default Index;
