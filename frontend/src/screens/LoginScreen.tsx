import React, { useState } from "react";
import {
  View,
  Text,
  TouchableOpacity,
  StyleSheet,
  KeyboardAvoidingView,
  Platform,
  ScrollView,
  ActivityIndicator,
  Alert,
  useWindowDimensions,
} from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";
import { StatusBar } from "expo-status-bar";
import TextInput from "../components/TextInput";
import { colors, fontSize, spacing, borderRadius } from "../constants/theme";
import type { LoginFormData } from "../types/auth";

const CARD_MAX_WIDTH = 420;

export default function LoginScreen() {
  const { width } = useWindowDimensions();
  const isWeb = Platform.OS === "web";
  const cardWidth = isWeb ? Math.min(width / 3, CARD_MAX_WIDTH) : undefined;
  const [form, setForm] = useState<LoginFormData>({
    username: "",
    email: "",
    firstName: "",
    lastName: "",
  });
  const [usernameError, setUsernameError] = useState("");
  const [loading, setLoading] = useState(false);

  const updateField = (field: keyof LoginFormData, value: string) => {
    setForm((prev) => ({ ...prev, [field]: value }));
    if (field === "username" && usernameError) {
      setUsernameError("");
    }
  };

  const handleLogin = () => {
    if (!form.username.trim()) {
      setUsernameError("Username is required");
      return;
    }

    setLoading(true);

    // TODO: Integrate with Keycloak OIDC
    setTimeout(() => {
      setLoading(false);
      Alert.alert("Login", `Logging in as ${form.username}`);
    }, 1000);
  };

  return (
    <SafeAreaView style={styles.container}>
      <StatusBar style="light" />
      <KeyboardAvoidingView
        style={styles.flex}
        behavior={Platform.OS === "ios" ? "padding" : "height"}
      >
        <ScrollView
          contentContainerStyle={styles.scrollContent}
          keyboardShouldPersistTaps="handled"
        >
          <View
            style={[
              styles.card,
              isWeb && { width: cardWidth },
            ]}
          >
            <View style={styles.header}>
              <Text style={styles.title}>Sign In</Text>
              <Text style={styles.subtitle}>
                Enter your credentials to continue
              </Text>
            </View>

            <View style={styles.form}>
            <TextInput
              label="Username"
              required
              placeholder="Enter your username"
              value={form.username}
              onChangeText={(v) => updateField("username", v)}
              error={usernameError}
              autoCapitalize="none"
              autoCorrect={false}
              returnKeyType="next"
            />

            <TextInput
              label="Email"
              placeholder="Enter your email"
              value={form.email}
              onChangeText={(v) => updateField("email", v)}
              keyboardType="email-address"
              autoCapitalize="none"
              autoCorrect={false}
              returnKeyType="next"
            />

            <View style={styles.row}>
              <View style={styles.halfField}>
                <TextInput
                  label="First Name"
                  placeholder="First name"
                  value={form.firstName}
                  onChangeText={(v) => updateField("firstName", v)}
                  returnKeyType="next"
                />
              </View>
              <View style={styles.halfField}>
                <TextInput
                  label="Last Name"
                  placeholder="Last name"
                  value={form.lastName}
                  onChangeText={(v) => updateField("lastName", v)}
                  returnKeyType="done"
                  onSubmitEditing={handleLogin}
                />
              </View>
            </View>

            <TouchableOpacity
              style={[styles.button, loading && styles.buttonDisabled]}
              onPress={handleLogin}
              activeOpacity={0.8}
              disabled={loading}
            >
              {loading ? (
                <ActivityIndicator color={colors.text} />
              ) : (
                <Text style={styles.buttonText}>Sign In</Text>
              )}
            </TouchableOpacity>
            </View>
          </View>
        </ScrollView>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: colors.background,
  },
  flex: {
    flex: 1,
  },
  scrollContent: {
    flexGrow: 1,
    justifyContent: "center",
    alignItems: "center",
    paddingHorizontal: spacing.lg,
  },
  card: {
    width: "100%",
    borderWidth: 1.5,
    borderColor: "#4FC3F7",
    borderRadius: borderRadius.lg,
    padding: spacing.xl,
    backgroundColor: colors.surface,
  },
  header: {
    marginBottom: spacing.xl,
  },
  title: {
    color: colors.text,
    fontSize: fontSize.xxl,
    fontWeight: "700",
    letterSpacing: 0.3,
  },
  subtitle: {
    color: colors.textSecondary,
    fontSize: fontSize.md,
    marginTop: spacing.xs,
  },
  form: {
    gap: spacing.xs,
  },
  row: {
    flexDirection: "row",
    gap: spacing.sm,
  },
  halfField: {
    flex: 1,
  },
  button: {
    backgroundColor: colors.accent,
    paddingVertical: 16,
    borderRadius: borderRadius.sm,
    alignItems: "center",
    justifyContent: "center",
    marginTop: spacing.md,
    minHeight: 52,
  },
  buttonDisabled: {
    opacity: 0.7,
  },
  buttonText: {
    color: colors.text,
    fontSize: fontSize.lg,
    fontWeight: "600",
  },
});
