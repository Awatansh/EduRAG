import './globals.css';

export const metadata = {
  title: 'Edu Rag — Knowledge Base Assistant',
  description: 'Upload documents, ask questions, and generate quizzes with AI-powered RAG.',
};

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
