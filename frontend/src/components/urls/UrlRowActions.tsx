import { useNavigate } from "react-router-dom";
import { BarChart3, MoreHorizontal, Pencil, QrCode, Trash2 } from "lucide-react";

import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import type { Url } from "@/types/api";

interface UrlRowActionsProps {
  url: Url;
  onEdit: () => void;
  onDelete: () => void;
  onShowQr: () => void;
}

export function UrlRowActions({ url, onEdit, onDelete, onShowQr }: UrlRowActionsProps) {
  const navigate = useNavigate();

  return (
    <DropdownMenu>
      <DropdownMenuTrigger render={<Button variant="ghost" size="icon-sm" />}>
        <MoreHorizontal />
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end">
        <DropdownMenuItem onClick={() => navigate(`/urls/${url.short_code}/analytics`)}>
          <BarChart3 />
          View analytics
        </DropdownMenuItem>
        <DropdownMenuItem onClick={onShowQr}>
          <QrCode />
          QR code
        </DropdownMenuItem>
        <DropdownMenuItem onClick={onEdit}>
          <Pencil />
          Edit
        </DropdownMenuItem>
        <DropdownMenuItem variant="destructive" onClick={onDelete}>
          <Trash2 />
          Delete
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  );
}
