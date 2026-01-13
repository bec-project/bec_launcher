pragma Singleton
import QtQuick

QtObject {
    // ─────────────────────────────────────────────────────────
    // Background colors
    // ─────────────────────────────────────────────────────────
    readonly property color background: "#0e1017"
    readonly property color backgroundCard: "#161921"
    readonly property color backgroundCardHover: "#1c2029"
    readonly property color backgroundCardSelected: "#1f2533"
    readonly property color backgroundInput: "#0d1015"
    readonly property color backgroundPopup: "#151922"

    // ─────────────────────────────────────────────────────────
    // Border colors
    // ─────────────────────────────────────────────────────────
    readonly property color border: "#2b3342"
    readonly property color borderHover: "#3a4556"
    readonly property color borderFocus: "#3daee9"
    readonly property color borderSelected: "#3daee9"

    // ─────────────────────────────────────────────────────────
    // Text colors
    // ─────────────────────────────────────────────────────────
    readonly property color textPrimary: "#ffffff"
    readonly property color textSecondary: "#b8c0cc"
    readonly property color textMuted: "#6b7280"
    readonly property color textDisabled: "#4b5563"

    // ─────────────────────────────────────────────────────────
    // Accent / brand colors
    // ─────────────────────────────────────────────────────────
    readonly property color accent: "#3daee9"
    readonly property color accentHover: "#52b8eb"
    readonly property color accentPressed: "#2a9cd8"

    // ─────────────────────────────────────────────────────────
    // Status / badge colors
    // ─────────────────────────────────────────────────────────
    readonly property color badgeProd: "#22c55e"
    readonly property color badgeProdBg: Qt.rgba(34/255, 197/255, 94/255, 0.15)
    readonly property color badgeTest: "#f59e0b"
    readonly property color badgeTestBg: Qt.rgba(245/255, 158/255, 11/255, 0.15)
    readonly property color badgeDev: "#3b82f6"
    readonly property color badgeDevBg: Qt.rgba(59/255, 130/255, 246/255, 0.15)

    // ─────────────────────────────────────────────────────────
    // Button colors
    // ─────────────────────────────────────────────────────────
    readonly property color buttonPrimary: "#3daee9"
    readonly property color buttonPrimaryHover: "#52b8eb"
    readonly property color buttonSecondary: "#1f2937"
    readonly property color buttonSecondaryHover: "#374151"

    // ─────────────────────────────────────────────────────────
    // Misc
    // ─────────────────────────────────────────────────────────
    readonly property color shadow: "#000000"
    readonly property color divider: "#2b3342"
    readonly property color success: "#22c55e"
    readonly property color warning: "#f59e0b"
    readonly property color error: "#ef4444"

    // ─────────────────────────────────────────────────────────
    // Dimensions
    // ─────────────────────────────────────────────────────────
    readonly property int radiusSmall: 6
    readonly property int radiusMedium: 10
    readonly property int radiusLarge: 14

    readonly property int spacingSmall: 8
    readonly property int spacingMedium: 12
    readonly property int spacingLarge: 16

    // ─────────────────────────────────────────────────────────
    // Animation durations
    // ─────────────────────────────────────────────────────────
    readonly property int animFast: 120
    readonly property int animNormal: 200
    readonly property int animSlow: 350
}
