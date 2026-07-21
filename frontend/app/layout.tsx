import type { Metadata } from "next";
import { ClerkProvider, SignedIn, SignedOut, SignInButton, UserButton } from "@clerk/nextjs";
import "./globals.css";

export const metadata: Metadata = {
  title: "PromiseGuard",
  description: "AI-powered customer commitment intelligence",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <ClerkProvider>
      <html lang="en">
        <body className="bg-gray-50 text-gray-900 min-h-screen font-sans antialiased">
          <header className="bg-white border-b border-gray-200 px-6 py-0 flex items-center justify-between h-14 sticky top-0 z-50">
            <div className="flex items-center gap-2">
              <div className="w-7 h-7 rounded-lg bg-blue-600 flex items-center justify-center text-white text-sm">🛡️</div>
              <span className="text-base font-semibold tracking-tight text-gray-900">PromiseGuard</span>
              <span className="hidden sm:block text-xs text-gray-400 font-medium border-l border-gray-200 pl-2 ml-1">Commitment Intelligence</span>
            </div>
            <div className="flex items-center gap-3">
              <SignedOut>
                <SignInButton mode="modal">
                  <button className="text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 px-4 py-1.5 rounded-lg transition-colors">
                    Sign in
                  </button>
                </SignInButton>
              </SignedOut>
              <SignedIn>
                <UserButton afterSignOutUrl="/" />
              </SignedIn>
            </div>
          </header>
          <main className="max-w-5xl mx-auto px-6 py-10">{children}</main>
        </body>
      </html>
    </ClerkProvider>
  );
}
