import { Link } from "react-router-dom";
import { Button } from "@/components/ui/button";

export default function NotFoundPage() {
  return (
    <div className="flex min-h-screen flex-col items-center justify-center gap-3 text-center">
      <p className="text-6xl font-semibold">404</p>
      <p className="text-muted-foreground">This page doesn&apos;t exist.</p>
      <Button render={<Link to="/" />}>Go home</Button>
    </div>
  );
}
