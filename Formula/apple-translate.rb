class AppleTranslate < Formula
  desc "CLI translation tool powered by Apple Translation API"
  homepage "https://github.com/taogya/AppleTranslateScript"
  url "https://github.com/taogya/AppleTranslateScript/archive/refs/tags/v1.1.0.tar.gz"
  sha256 "77665c92a07c13f7b6fae1dcf832ef43220d61365585d2cc3e7d06e5142ef998"
  license "BSD-3-Clause"

  depends_on xcode: ["26.0", :build]
  depends_on :macos => :tahoe # macOS 26

  def install
    system "swift", "build",
           "-c", "release",
           "--disable-sandbox"
    bin.install ".build/release/apple-translate"
  end

  def caveats
    <<~EOS
      After installation, refresh your shell's hash table:

        hash -r

      Translation language packs are required. Download them in advance:

        System Settings > General > Translation Languages
    EOS
  end

  test do
    assert_match "apple-translate", shell_output("#{bin}/apple-translate --version")
  end
end
