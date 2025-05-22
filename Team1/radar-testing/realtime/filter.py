import numpy as np
from scipy.signal import butter
from scipy.signal import freqz
import scipy.signal as signal
import matplotlib.pyplot as plt
import unittest

class IIRFilter():
    def __init__(self, coeffs):
       self.b = coeffs[0:3] 
       self.a = coeffs[4:]
       
       self.tb1 = 0
       self.tb2 = 0
       self.ta1 = 0
       self.ta2 = 0

    def filter(self, sample):
        accumulator  = sample   * self.b[0]
        accumulator += self.tb1 * self.b[1]
        accumulator += self.tb2 * self.b[2]
        accumulator -= self.ta1 * self.a[0]
        accumulator -= self.ta2 * self.a[1]

        self.tb2 = self.tb1
        self.tb1 = sample
        self.ta2 = self.ta1
        self.ta1 = accumulator

        return accumulator

class Filter():
    def __init__(self, fs, f_pass):
        coeffs = butter(2, f_pass, btype="lowpass", fs=fs, output="sos")
        self.__iirs = [IIRFilter(c) for c in coeffs]

    def filter(self, sample):
        for iir in self.__iirs: sample = iir.filter(sample)

        return sample

def test_filter():
    # test signal
    fs = 1000
    data = np.abs(np.fft.ifft(np.ones(fs)))

    # apply the filter
    out_data = []
    filter = Filter(fs, 50)
    for d in data:
        out_data.append(filter.filter(d))

    plt.plot(np.abs(np.fft.fft(data)) / len(data), label= 'Original FFT')
    plt.plot(np.abs(np.fft.fft(out_data) / len(out_data)), label= 'Filtered FFT')
    plt.xlabel("Frequency (Hz)")
    plt.ylabel("Amplitude")
    plt.title("FFT of Original and Filtered Signals")
    plt.legend()
    plt.grid()
    plt.show()

class FilterTest(unittest.TestCase):

    def gen_test_signal(self, fs):
        return np.abs(np.fft.ifft(np.ones(fs)))

    tolerance_places = 1

    # TEST PASSBAND PERFORMANCE
    def passband_attenuation(self, f_pass):
        fs = 1000
        signal = self.gen_test_signal(fs)

        filter = Filter(fs, f_pass)
        out_signal = [filter.filter(x) for x in signal]
        self.assertAlmostEqual(np.abs(np.fft.fft(out_signal))[f_pass], np.abs(np.fft.fft(signal))[f_pass], places=self.tolerance_places)

    def test_passband_attenuation_20Hz(self):
        self.passband_attenuation(20)
    
    def test_passband_attenuation_100Hz(self):
        self.passband_attenuation(100)

    def test_passband_attenuation_200Hz(self):
        self.passband_attenuation(200)


    # TEST INDIVIDUAL IIR PASSBAND PERFORMANCE
    def iir_passband_attenuation(self, f_pass):
        fs = 1000
        signal = self.gen_test_signal(fs)

        filter = IIRFilter(butter(1, [f_pass-5, f_pass+5], btype="bandpass", fs=fs, output="sos")[0])
        out_signal = [filter.filter(x) for x in signal]
        self.assertAlmostEqual(np.abs(np.fft.fft(out_signal))[f_pass], np.abs(np.fft.fft(signal))[f_pass], places=self.tolerance_places)

    def test_iir_passband_attenuation_20Hz(self):
        self.iir_passband_attenuation(20)
    
    def test_iir_passband_attenuation_100Hz(self):
        self.iir_passband_attenuation(100)

    def test_iir_passband_attenuation_200Hz(self):
        self.iir_passband_attenuation(200)


    # TEST STOPBAND PERFORMANCE
    def stopband_attenuation(self, f_pass):
        fs = 1000
        signal = self.gen_test_signal(fs)

        filter = Filter(fs, f_pass)
        out_signal = [filter.filter(x) for x in signal]

        for i in range(f_pass + 10, fs // 2):
            self.assertAlmostEqual(np.abs(np.fft.fft(out_signal))[i], 0, places=self.tolerance_places)
        for i in range(0, f_pass - 10):
            self.assertAlmostEqual(np.abs(np.fft.fft(out_signal))[i], 0, places=self.tolerance_places)

    def test_stopband_attenuation_20Hz(self):
        self.stopband_attenuation(20)
    
    def test_stopband_attenuation_100Hz(self):
        self.stopband_attenuation(100)

    def test_stopband_attenuation_200Hz(self):
        self.passband_attenuation(200)


if __name__ == "__main__":
    unittest.main()
