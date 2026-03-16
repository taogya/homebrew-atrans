class AppleTranslate < Formula
  desc "CLI translation tool powered by Apple Translation API"
  homepage "https://github.com/taogya/AppleTranslateScript"
  url "https://github.com/taogya/AppleTranslateScript/archive/refs/tags/v1.0.0.tar.gz"
  sha256 "d5558cd419c8d46bdc958064cb97f963d1ea793866414c025906ec15033512ed"
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
