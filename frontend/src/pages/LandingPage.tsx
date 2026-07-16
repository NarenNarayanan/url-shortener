import { Link } from "react-router-dom";
import { BarChart3, Link2, QrCode, ShieldCheck } from "lucide-react";

import { Button } from "@/components/ui/button";
import { ThemeToggle } from "@/components/ThemeToggle";

const features = [
  {
    icon: Link2,
    title: "Shorten instantly",
    description: "Turn any long URL into a clean, shareable link in one click.",
  },
  {
    icon: BarChart3,
    title: "Real analytics",
    description: "Daily and weekly click trends, plus browser, OS, and device breakdowns.",
  },
  {
    icon: QrCode,
    title: "QR codes built in",
    description: "Every link gets a downloadable QR code, ready for print or slides.",
  },
  {
    icon: ShieldCheck,
    title: "Secure by default",
    description: "JWT auth, rate limiting, and links that can auto-expire on your schedule.",
  },
];

export default function LandingPage() {
  return (
    <div className="min-h-screen">
      <header className="flex items-center justify-between px-6 py-4">
        <div className="flex items-center gap-2 font-semibold">
          <Link2 className="h-5 w-5" />
          Snip
        </div>
        <div className="flex items-center gap-2">
          <ThemeToggle />
          <Button variant="ghost" render={<Link to="/login" />}>
            Log in
          </Button>
          <Button render={<Link to="/register" />}>Sign up</Button>
        </div>
      </header>

      <main className="flex flex-col items-center gap-6 px-4 pt-16 pb-24 text-center">
        <h1 className="max-w-2xl text-4xl font-semibold tracking-tight sm:text-5xl">
          Shorten links. Track every click.
        </h1>
        <p className="max-w-md text-muted-foreground">
          A fast, no-nonsense URL shortener with real analytics — browser, OS, device, and time-series breakdowns for
          every link you create.
        </p>
        <div className="flex gap-3">
          <Button size="lg" render={<Link to="/register" />}>
            Get started — it&apos;s free
          </Button>
          <Button size="lg" variant="outline" render={<Link to="/login" />}>
            Log in
          </Button>
        </div>

        <div className="mt-16 grid w-full max-w-4xl gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {features.map((feature) => (
            <div key={feature.title} className="rounded-xl border bg-card p-5 text-left">
              <feature.icon className="h-5 w-5 text-muted-foreground" />
              <p className="mt-3 font-medium">{feature.title}</p>
              <p className="mt-1 text-sm text-muted-foreground">{feature.description}</p>
            </div>
          ))}
        </div>
      </main>
    </div>
  );
}
