import { useEffect, useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { Loader2 } from "lucide-react";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { urlsApi } from "@/lib/api";
import { extractErrorMessage } from "@/lib/api-client";
import { fromDatetimeLocalValue, toDatetimeLocalValue } from "@/lib/date-utils";
import { urlFormSchema, type UrlFormValues } from "@/lib/validation";
import type { Url } from "@/types/api";

interface UrlFormDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  /** Present for edit mode, absent for create mode. */
  url?: Url;
}

export function UrlFormDialog({ open, onOpenChange, url }: UrlFormDialogProps) {
  const isEditMode = Boolean(url);
  const queryClient = useQueryClient();
  const [isSubmitting, setIsSubmitting] = useState(false);

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors },
  } = useForm<UrlFormValues>({ resolver: zodResolver(urlFormSchema) });

  // Re-seed the form whenever a different URL is opened for editing, or when
  // switching back to "create" (blank form).
  useEffect(() => {
    if (open) {
      reset({
        original_url: url?.original_url ?? "",
        expires_at: toDatetimeLocalValue(url?.expires_at),
      });
    }
  }, [open, url, reset]);

  const createMutation = useMutation({
    mutationFn: urlsApi.create,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["urls"] });
      toast.success("Short link created");
      onOpenChange(false);
    },
    onError: (error) => toast.error(extractErrorMessage(error)),
  });

  const updateMutation = useMutation({
    mutationFn: (values: UrlFormValues) =>
      urlsApi.update(url!.short_code, {
        original_url: values.original_url,
        expires_at: fromDatetimeLocalValue(values.expires_at),
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["urls"] });
      toast.success("Link updated");
      onOpenChange(false);
    },
    onError: (error) => toast.error(extractErrorMessage(error)),
  });

  async function onSubmit(values: UrlFormValues) {
    setIsSubmitting(true);
    try {
      if (isEditMode) {
        await updateMutation.mutateAsync(values);
      } else {
        await createMutation.mutateAsync({
          original_url: values.original_url,
          expires_at: fromDatetimeLocalValue(values.expires_at),
        });
      }
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>{isEditMode ? "Edit link" : "Create a short link"}</DialogTitle>
          <DialogDescription>
            {isEditMode
              ? "Update the destination or expiration for this link."
              : "Paste a long URL to get a short, shareable link."}
          </DialogDescription>
        </DialogHeader>

        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4" noValidate>
          <div className="space-y-1.5">
            <Label htmlFor="original_url">Destination URL</Label>
            <Input
              id="original_url"
              placeholder="https://example.com/a/very/long/path"
              aria-invalid={Boolean(errors.original_url)}
              {...register("original_url")}
            />
            {errors.original_url && <p className="text-xs text-destructive">{errors.original_url.message}</p>}
          </div>

          <div className="space-y-1.5">
            <Label htmlFor="expires_at">Expires at (optional)</Label>
            <Input id="expires_at" type="datetime-local" {...register("expires_at")} />
            <p className="text-xs text-muted-foreground">Leave blank for a link that never expires.</p>
          </div>

          <DialogFooter>
            <Button type="submit" disabled={isSubmitting}>
              {isSubmitting && <Loader2 className="h-4 w-4 animate-spin" />}
              {isEditMode ? "Save changes" : "Create link"}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
