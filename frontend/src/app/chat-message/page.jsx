import Breadcrumb from "@/components/Breadcrumb";
import ChatMessageLayer from "@/components/ChatMessageLayer";
import MasterLayout from "@/masterLayout/MasterLayout";

export const metadata = {
  title: "Serve Well ",
  description:
    "Serve Well is a web application that provides a comprehensive solution for managing and tracking service requests, ensuring efficient communication between service providers and customers.",
};

const Page = () => {
  return (
    <>
      {/* MasterLayout */}
      <MasterLayout>
        {/* Breadcrumb */}
        <Breadcrumb title='Chat Message' />

        {/* ChatMessageLayer */}
        <ChatMessageLayer />
      </MasterLayout>
    </>
  );
};

export default Page;
