import { ReactNode } from 'react';
import { motion } from 'framer-motion';

interface LayoutProps {
  children: ReactNode;
}

export default function Layout({ children }: LayoutProps) {
  return (
    <div className="min-h-screen flex flex-col">
      {/* Header */}
      <header className="bg-hoop-blue text-hoop-white shadow-lg">
        <div className="container mx-auto px-4 py-4 flex justify-between items-center">
          <div className="flex items-center space-x-2">
            <BasketballIcon className="h-8 w-8 text-hoop-yellow" />
            <h1 className="text-2xl font-display tracking-tight">HoopNarrator</h1>
          </div>
          <nav>
            <ul className="flex space-x-6">
              <li><a href="#" className="hover:text-hoop-yellow transition-colors">Home</a></li>
              <li><a href="#" className="hover:text-hoop-yellow transition-colors">About</a></li>
              <li><a href="#" className="hover:text-hoop-yellow transition-colors">How It Works</a></li>
            </ul>
          </nav>
        </div>
      </header>

      {/* Main content */}
      <main className="flex-grow">
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 0.5 }}
          className="container mx-auto px-4 py-8"
        >
          {children}
        </motion.div>
      </main>

      {/* Footer */}
      <footer className="bg-hoop-gray-900 text-hoop-white py-6">
        <div className="container mx-auto px-4 text-center">
          <p>© {new Date().getFullYear()} HoopNarrator. All rights reserved.</p>
        </div>
      </footer>
    </div>
  );
}

// Simple basketball icon component
function BasketballIcon({ className }: { className?: string }) {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      viewBox="0 0 24 24"
      fill="currentColor"
      className={className}
    >
      <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm0 18c-4.42 0-8-3.58-8-8s3.58-8 8-8 8 3.58 8 8-3.58 8-8 8z" />
      <path d="M7.07 8.17c.39.39 1.02.39 1.41 0 .39-.39.39-1.02 0-1.41-.39-.39-1.02-.39-1.41 0-.39.39-.39 1.03 0 1.41zM12 15.5c-1.93 0-3.5-1.57-3.5-3.5s1.57-3.5 3.5-3.5 3.5 1.57 3.5 3.5-1.57 3.5-3.5 3.5zm0-5c-.83 0-1.5.67-1.5 1.5s.67 1.5 1.5 1.5 1.5-.67 1.5-1.5-.67-1.5-1.5-1.5zm4.53 4.12c-.2.2-.2.51 0 .71.2.2.51.2.71 0l1.41-1.41c.2-.2.2-.51 0-.71-.2-.2-.51-.2-.71 0l-1.41 1.41z" />
    </svg>
  );
}
