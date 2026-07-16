import { useState } from "react";
import { Check, Copy } from "lucide-react";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";

export function CopyButton({ value }: { value: string }) {
  const [justCopied, setJustCopied] = useState(false);

  async function handleCopy() {
    try {
      await navigator.clipboard.writeText(value);
      setJustCopied(true);
      toast.success("Copied to clipboard");
      setTimeout(() => setJustCopied(false), 1500);
    } catch {
      toast.error("Couldn't copy — your browser blocked clipboard access");
    }
  }

  return (
    <Button variant="ghost" size="icon-sm" onClick={handleCopy} aria-label="Copy link">
      {justCopied ? <Check className="text-green-600" /> : <Copy />}
    </Button>
  );
}
