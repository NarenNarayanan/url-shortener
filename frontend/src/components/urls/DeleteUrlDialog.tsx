import { useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { Loader2 } from "lucide-react";
import { toast } from "sonner";

import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog";
import { urlsApi } from "@/lib/api";
import { extractErrorMessage } from "@/lib/api-client";
import type { Url } from "@/types/api";

interface DeleteUrlDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  url: Url | null;
}

export function DeleteUrlDialog({ open, onOpenChange, url }: DeleteUrlDialogProps) {
  const queryClient = useQueryClient();
  const [isDeleting, setIsDeleting] = useState(false);

  const deleteMutation = useMutation({
    mutationFn: (shortCode: string) => urlsApi.remove(shortCode),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["urls"] });
      toast.success("Link deleted");
      onOpenChange(false);
    },
    onError: (error) => toast.error(extractErrorMessage(error)),
  });

  async function handleConfirm() {
    if (!url) return;
    setIsDeleting(true);
    try {
      await deleteMutation.mutateAsync(url.short_code);
    } finally {
      setIsDeleting(false);
    }
  }

  return (
    <AlertDialog open={open} onOpenChange={onOpenChange}>
      <AlertDialogContent>
        <AlertDialogHeader>
          <AlertDialogTitle>Delete this link?</AlertDialogTitle>
          <AlertDialogDescription>
            <span className="font-medium text-foreground">{url?.short_url}</span> will stop working immediately.
            This can&apos;t be undone.
          </AlertDialogDescription>
        </AlertDialogHeader>
        <AlertDialogFooter>
          <AlertDialogCancel disabled={isDeleting}>Cancel</AlertDialogCancel>
          <AlertDialogAction
            variant="destructive"
            onClick={handleConfirm}
            disabled={isDeleting}
          >
            {isDeleting && <Loader2 className="h-4 w-4 animate-spin" />}
            Delete
          </AlertDialogAction>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
  );
}
