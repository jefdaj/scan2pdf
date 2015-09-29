{ stdenv
, buildPythonPackage
, fetchgit
, imagemagick
, netpbm
, python3
, saneBackends
}:

buildPythonPackage rec {
  version = "0.2";
  name = "scan2pdf-${version}";
  src = ./.;
  buildPrefix = "";
  buildInputs = [ 
    imagemagick
    netpbm
    python3
    saneBackends
  ];
  meta = {
    homepage = "https://github.com/jefdaj/scan2pdf";
    description = "A script to automate scanning documents.";
  };
}
