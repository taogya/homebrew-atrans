class AppleTranslate < Formula
  desc "CLI translation tool powered by Apple Translation API"
  homepage "https://github.com/taogya/AppleTranslateScript"
  url "https://github.com/taogya/AppleTranslateScript/archive/refs/tags/v1.0.0.tar.gz"
  sha256 "" # リリース時に `shasum -a 256 <tarball>` で取得して差し替え
  license "BSD-3-Clause"

  depends_on xcode: ["26.0", :build]
  depends_on :macos => :tahoe # macOS 26

  def install
    system "swift", "build",
           "-c", "release",
           "--disable-sandbox"
    bin.install ".build/release/apple-translate"
  end

  test do
    assert_match "apple-translate", shell_output("#{bin}/apple-translate --version")
  end
end
