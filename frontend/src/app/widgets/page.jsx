import Breadcrumb from "@/components/Breadcrumb";
import WidgetsLayer from "@/components/WidgetsLayer";
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
        <Breadcrumb title='Wallet' />

        {/* WidgetsLayer */}
        <WidgetsLayer />
      </MasterLayout>
    </>
  );
};

export default Page;
