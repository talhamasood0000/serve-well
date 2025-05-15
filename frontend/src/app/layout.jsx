import PluginInit from "@/helper/PluginInit";
import "./font.css";
import "./globals.css";

export const metadata = {
  title: "Serve Well ",
  description:
    "Serve Well is a web application that provides a comprehensive solution for managing and tracking service requests, ensuring efficient communication between service providers and customers.",
};

export default function RootLayout({ children }) {
  return (
    <html lang='en'>
      <PluginInit />
      <body suppressHydrationWarning={true}>{children}</body>
    </html>
  );
}
