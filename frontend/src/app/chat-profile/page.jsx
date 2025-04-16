import Breadcrumb from "@/components/Breadcrumb";
import ChatProfileLayer from "@/components/ChatProfileLayer";
import MasterLayout from "@/masterLayout/MasterLayout";

export const metadata = {
  title: "Chat Profile | ServeWell AI Platform",
  description: "Manage and view user chat profiles and conversation history in the ServeWell AI customer service platform.",
};

const Page = () => {
  return (
    <>
      {/* MasterLayout */}
      <MasterLayout>
        {/* Breadcrumb */}
        <Breadcrumb title='Chat' />

        {/* ChatProfileLayer */}
        <ChatProfileLayer />
      </MasterLayout>
    </>
  );
};

export default Page;
