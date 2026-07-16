import { z } from "zod";

// These mirror the constraints in backend/app/schemas/*.py — kept in sync
// so the form gives instant feedback instead of waiting on a round trip.

export const loginSchema = z.object({
  email: z.string().min(1, "Email is required").email("Enter a valid email address"),
  password: z.string().min(1, "Password is required"),
});
export type LoginFormValues = z.infer<typeof loginSchema>;

export const registerSchema = z.object({
  username: z.string().min(3, "At least 3 characters").max(50, "At most 50 characters"),
  email: z.string().min(1, "Email is required").email("Enter a valid email address"),
  password: z.string().min(8, "At least 8 characters").max(128, "At most 128 characters"),
});
export type RegisterFormValues = z.infer<typeof registerSchema>;

export const urlFormSchema = z.object({
  original_url: z.string().min(1, "URL is required").url("Enter a valid URL, including https://"),
  expires_at: z.string().optional(),
});
export type UrlFormValues = z.infer<typeof urlFormSchema>;
