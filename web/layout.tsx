import "./globals.css";

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="h-full">
      <head>
        <title>Recipe Box Lite</title>
        <meta name="description" content="A simple, privacy‑first digital cookbook." />
      </head>
      <body className="min-h-full bg-gray-50 p-4">
        {children}
      </body>
    </html>
  );
}