import { QRCodeSVG } from "qrcode.react";
import { Download } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import type { Url } from "@/types/api";

interface QrCodeDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  url: Url | null;
}

export function QrCodeDialog({ open, onOpenChange, url }: QrCodeDialogProps) {
  function handleDownload() {
    if (!url) return;
    const svg = document.getElementById(`qr-${url.short_code}`);
    if (!svg) return;

    const svgData = new XMLSerializer().serializeToString(svg);
    const canvas = document.createElement("canvas");
    canvas.width = 512;
    canvas.height = 512;
    const ctx = canvas.getContext("2d")!;
    const img = new Image();
    img.onload = () => {
      ctx.fillStyle = "#ffffff";
      ctx.fillRect(0, 0, canvas.width, canvas.height);
      ctx.drawImage(img, 0, 0, canvas.width, canvas.height);
      const link = document.createElement("a");
      link.download = `qr-${url.short_code}.png`;
      link.href = canvas.toDataURL("image/png");
      link.click();
    };
    img.src = `data:image/svg+xml;base64,${btoa(unescape(encodeURIComponent(svgData)))}`;
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>QR code</DialogTitle>
        </DialogHeader>
        {url && (
          <div className="flex flex-col items-center gap-4 py-2">
            <div className="rounded-lg border bg-white p-4">
              <QRCodeSVG id={`qr-${url.short_code}`} value={url.short_url} size={200} />
            </div>
            <p className="text-sm text-muted-foreground">{url.short_url}</p>
            <Button variant="outline" onClick={handleDownload}>
              <Download />
              Download PNG
            </Button>
          </div>
        )}
      </DialogContent>
    </Dialog>
  );
}
